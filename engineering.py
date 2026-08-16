"""
engineering.py
================
Core object-oriented engineering library for the Fluid Flow & Heat Transfer
Engineering Suite (PE 262 Capstone Project).

Classes
-------
Fluid                 : a Newtonian fluid with density/viscosity properties.
Pipe                  : a circular pipe section with flow/pressure-drop physics.
HeatTransferAnalysis  : steady-state conduction and Newton's Law of Cooling.

All classes are self-contained, unit-tested against hand calculations (see
each page's "verified against" note), and raise clear ValueErrors on
physically invalid input so calling code (the Streamlit pages) can catch
them and show a warning instead of crashing.
"""

import math


class Fluid:
    """A Newtonian fluid with key thermophysical properties.

    Attributes:
        name (str): fluid identifier, e.g. "water".
        density (float): fluid density, kg/m3.
        viscosity (float): dynamic viscosity, Pa.s (kg/m.s).
    """

    #: Reference properties for common fluids at ~20 C, used to auto-populate
    #: the Pipe Flow Analyser's fluid selector.
    LIBRARY = {
        "Water": {"density": 998.0, "viscosity": 0.001},
        "Air": {"density": 1.225, "viscosity": 1.81e-5},
        "Crude Oil": {"density": 850.0, "viscosity": 0.005},
    }

    def __init__(self, name: str, density: float, viscosity: float):
        """
        Args:
            name: fluid identifier (str).
            density: fluid density in kg/m3 (float, must be > 0).
            viscosity: dynamic viscosity in Pa.s (float, must be > 0).

        Raises:
            ValueError: if density or viscosity is not strictly positive.
        """
        if density <= 0:
            raise ValueError("Fluid density must be greater than 0 kg/m3.")
        if viscosity <= 0:
            raise ValueError("Fluid viscosity must be greater than 0 Pa.s.")
        self.name = name
        self.density = density
        self.viscosity = viscosity

    def kinematic_viscosity(self) -> float:
        """Return kinematic viscosity nu = mu / rho, in m2/s."""
        return self.viscosity / self.density

    def reynolds(self, velocity: float, diameter: float) -> float:
        """Return the Reynolds number Re = rho * v * D / mu (dimensionless).

        Args:
            velocity: mean flow velocity, m/s.
            diameter: pipe internal diameter, m.
        """
        return self.density * velocity * diameter / self.viscosity

    def flow_regime(self, velocity: float, diameter: float) -> str:
        """Classify the flow as Laminar, Transitional, or Turbulent.

        Uses the standard pipe-flow thresholds Re < 2300 (laminar) and
        Re > 4000 (turbulent), with the range in between called transitional.
        """
        re = self.reynolds(velocity, diameter)
        if re < 2300:
            return "Laminar"
        elif re < 4000:
            return "Transitional"
        return "Turbulent"

    def __repr__(self):
        return f"Fluid('{self.name}', rho={self.density}, mu={self.viscosity})"


class Pipe:
    """A circular pipe section, used for Darcy-Weisbach pressure-drop analysis.

    Attributes:
        D (float): internal diameter, m.
        L (float): pipe length, m.
        eps (float): absolute pipe-wall roughness, m.
    """

    def __init__(self, diameter: float, length: float, roughness: float = 0.000046):
        """
        Args:
            diameter: internal pipe diameter, m (must be > 0).
            length: pipe length, m (must be > 0).
            roughness: absolute wall roughness, m (default 0.000046 m,
                a typical value for commercial steel pipe).

        Raises:
            ValueError: if diameter, length, or roughness is not > 0
                (roughness may be exactly 0 for an ideally smooth pipe).
        """
        if diameter <= 0:
            raise ValueError("Pipe diameter must be greater than 0 m.")
        if length <= 0:
            raise ValueError("Pipe length must be greater than 0 m.")
        if roughness < 0:
            raise ValueError("Pipe roughness cannot be negative.")
        self.D = diameter
        self.L = length
        self.eps = roughness

    def area(self) -> float:
        """Return the internal cross-sectional flow area, m2."""
        return math.pi * (self.D / 2) ** 2

    def velocity(self, Q: float) -> float:
        """Return mean flow velocity for volumetric flow rate Q (m3/s), in m/s."""
        if Q < 0:
            raise ValueError("Flow rate Q cannot be negative.")
        return Q / self.area()

    def friction_factor(self, fluid: Fluid, Q: float) -> float:
        """Return the Darcy friction factor f (dimensionless).

        Uses f = 64/Re for laminar flow (Re < 2300), and solves the
        implicit Colebrook-White equation by fixed-point (Newton-Raphson)
        iteration for transitional/turbulent flow:

            1/sqrt(f) = -2*log10( eps/(3.7*D) + 2.51/(Re*sqrt(f)) )

        This matches the "use the Colebrook equation for turbulent flow"
        guidance from PE 262 Week 3, rather than assuming a fixed f=0.02.
        """
        v = self.velocity(Q)
        if v == 0:
            return 0.0
        re = fluid.reynolds(v, self.D)

        if re < 2300:
            return 64 / re

        # Swamee-Jain explicit approximation as the initial guess...
        f = 0.25 / (math.log10(self.eps / (3.7 * self.D) + 5.74 / re ** 0.9)) ** 2
        # ...then refine with a few Colebrook-White fixed-point iterations.
        for _ in range(20):
            rhs = -2 * math.log10(self.eps / (3.7 * self.D) + 2.51 / (re * math.sqrt(f)))
            f_new = 1 / rhs ** 2
            if abs(f_new - f) < 1e-8:
                f = f_new
                break
            f = f_new
        return f

    def pressure_drop(self, fluid: Fluid, Q: float) -> float:
        """Return the Darcy-Weisbach pressure drop over the pipe length, Pa.

            dP = f * (L/D) * rho * v^2 / 2
        """
        v = self.velocity(Q)
        f = self.friction_factor(fluid, Q)
        return f * (self.L / self.D) * fluid.density * v ** 2 / 2

    def report(self, fluid: Fluid, Q: float) -> dict:
        """Return a dict summarising velocity, Re, friction factor and
        pressure drop for the given fluid and flow rate Q (m3/s)."""
        v = self.velocity(Q)
        re = fluid.reynolds(v, self.D)
        f = self.friction_factor(fluid, Q)
        dp = self.pressure_drop(fluid, Q)
        return {
            "velocity_m_s": v,
            "reynolds": re,
            "flow_regime": fluid.flow_regime(v, self.D),
            "friction_factor": f,
            "pressure_drop_Pa": dp,
            "pressure_drop_bar": dp / 1e5,
        }

    def __repr__(self):
        return f"Pipe(D={self.D}, L={self.L}, eps={self.eps})"


class HeatTransferAnalysis:
    """Steady-state conduction and Newton's Law of Cooling calculations.

    Grouped as a class (rather than loose functions) so a single object can
    be configured once and reused for both the conduction check and the
    cooling-curve plot on the Heat Transfer Calculator page.
    """

    def __init__(self):
        pass

    @staticmethod
    def conduction_heat_flux(k: float, thickness: float, T_hot: float, T_cold: float) -> float:
        """Return steady-state conduction heat flux through a single flat
        wall layer using Fourier's Law, in W/m2:

            q'' = k * (T_hot - T_cold) / L

        Args:
            k: thermal conductivity of the wall material, W/(m.K).
            thickness: wall thickness L, m.
            T_hot: temperature on the hot face, deg C (or K, consistent).
            T_cold: temperature on the cold face, same units as T_hot.

        Raises:
            ValueError: if k or thickness is not strictly positive.
        """
        if k <= 0:
            raise ValueError("Thermal conductivity k must be greater than 0 W/(m.K).")
        if thickness <= 0:
            raise ValueError("Wall thickness must be greater than 0 m.")
        return k * (T_hot - T_cold) / thickness

    @staticmethod
    def conduction_heat_rate(k: float, thickness: float, area: float,
                              T_hot: float, T_cold: float) -> float:
        """Return the total steady-state conduction heat transfer rate, W:

            Q = k * A * (T_hot - T_cold) / L
        """
        if area <= 0:
            raise ValueError("Wall area must be greater than 0 m2.")
        q_flux = HeatTransferAnalysis.conduction_heat_flux(k, thickness, T_hot, T_cold)
        return q_flux * area

    @staticmethod
    def cooling_rate_constant(h: float, area: float, mass: float, specific_heat: float) -> float:
        """Return the lumped-capacitance cooling rate constant, 1/s:

            k_cool = h * A / (m * c)

        This is the exponent in Newton's Law of Cooling, T(t) = T_inf +
        (T0 - T_inf) * exp(-k_cool * t).

        Raises:
            ValueError: if any input is not strictly positive.
        """
        if h <= 0:
            raise ValueError("Convection coefficient h must be greater than 0 W/(m2.K).")
        if area <= 0:
            raise ValueError("Surface area must be greater than 0 m2.")
        if mass <= 0:
            raise ValueError("Mass must be greater than 0 kg.")
        if specific_heat <= 0:
            raise ValueError("Specific heat must be greater than 0 J/(kg.K).")
        return (h * area) / (mass * specific_heat)

    @staticmethod
    def temperature_at_time(t: float, T0: float, T_inf: float, k_cool: float) -> float:
        """Return object temperature at time t (s) under Newton's Law of
        Cooling:

            T(t) = T_inf + (T0 - T_inf) * exp(-k_cool * t)
        """
        return T_inf + (T0 - T_inf) * math.exp(-k_cool * t)

    @staticmethod
    def time_to_reach_target(T0: float, T_inf: float, T_target: float, k_cool: float) -> float:
        """Return the time (s) required to cool/heat from T0 to T_target in
        ambient temperature T_inf, by inverting Newton's Law of Cooling:

            t = -ln( (T_target - T_inf) / (T0 - T_inf) ) / k_cool

        Raises:
            ValueError: if T_target is not strictly between T0 and T_inf
                (i.e. physically unreachable), or if T0 equals T_inf.
        """
        if T0 == T_inf:
            raise ValueError("Initial temperature T0 must differ from ambient T_inf.")
        ratio = (T_target - T_inf) / (T0 - T_inf)
        if ratio <= 0 or ratio >= 1:
            raise ValueError(
                "Target temperature must lie strictly between the ambient "
                "temperature and the initial temperature."
            )
        return -math.log(ratio) / k_cool

    def __repr__(self):
        return "HeatTransferAnalysis()"
