# What is Lattice Boltzman methods and Why do we need it ?
from *"The Lattice Boltzman Method, Principles and Practice" - Timm Kruger*

- Fluid dynamics is primarily concerned with *macroscopic* description of fluids, which in itself implies a continumm theory 
- That is to say, under the assumption that Knudsen number is less than 0.01, we can treat fluids as temporal and spatial vector fieds, that are continuous functions of space and time - basically no holes in the fluids !
- LB methods are fundamentally different from Navier-Stokes models because they model fluids at a different scale 

- The differnt scales in a fluid flow can be summarised as $L_{molecules} < L_{meanfreepath}< L_{domain}$

- The middle scale which can be considered to have bundles of molecules is called the *Mesoscopic* Scale and that's where Lattice Boltzman methods exists.

## Kinetic Theory 
- The mesoscopic scale is primarily modelled by the framework of kinetic theory, which is neither interested in per particle discription or the macroscopic properties like densities,
- rather it is interested in modelling the distribution of molecules 
- Here the primary function to track is the *Distribution Function* $f(x,\epsilon, t)$
  - which can be understood as the generalisation of density $\rho$ 
  - but taking microscopic particle velocity into account 
  - It represents the mass in physical space and velocity space simultaneously 
  - The macroscopic properties of the fluids are related to this function by it's moments for ex: $\rho(x,t) = \int f(x,\epsilon,t)d^3\epsilon$
- Due to collisions eventually leading to angularly uniform particles we can propose the existence of a equillibrium distribution $f_{eq}(x,\epsilon,t)$

### Boltzmann Equation
$\frac{\partial{f}}{\partial{t}} + \zeta \frac{\partial{f}}{\partial{x}} + \frac{F}{\rho} \frac{\partial{f}}{\partial{\zeta}} = \Omega(f)  $

## Particle based Numerical Simulation Solver
- Conventional finite difference and finit volume solvers, discritize the continumm equations on finite points or volumes and eventually solving a linear equation of the form $Ax=b$ 
- particle based solvers model the fluid as particles (which can range from atoms to molecules to collection of molecules)
- There are multiple particle based methods but I'll skip to LBM for now

## Lattice Boltzman Method
- 