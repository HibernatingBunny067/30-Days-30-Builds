#pragma once
#include <cstdint>
#include <vector>

#include "lattice.hpp"

// 2D wind tunnel on a D2Q9 lattice. Flow enters at x = 0 with speed u0.
//
// Memory layout ("structure of arrays"): population q of cell (x, y) lives at
//   f[q * nx * ny + y * nx + x]
// so each direction is one contiguous nx*ny plane, which keeps streaming
// cache-friendly. Use idx(q, x, y) rather than writing that out by hand.
class Simulation {
 public:
  Simulation(int nx, int ny, float u0, float viscosity);

  void addCylinder(float cx, float cy, float radius);
  void reset();               // uniform free stream everywhere (fluid cells)
  void step();                // one full LBM time step
  bool isFinite() const;      // false once the simulation has blown up

  // Macroscopic fields, recomputed by computeMacroscopic(). Size nx*ny.
  void computeMacroscopic();
  std::vector<float> vorticity() const;
  std::vector<float> speed() const;

  int nx() const { return nx_; }
  int ny() const { return ny_; }
  long steps() const { return steps_; }
  float omega() const { return 1.0f / (3.0f * viscosity_ + 0.5f); }
  const std::vector<uint8_t>& obstacle() const { return obstacle_; }

 private:
  // The four pieces of an LBM step. Each is a TODO for you to implement;
  // the matching Python lives in python/solver/lbm.py.
  void collide();          // f += omega * (feq - f) on fluid cells
  void stream();           // move every population one cell along (ex, ey)
  void bounceBack();       // reverse populations inside obstacle cells
  void applyBoundaries();  // inlet (left), outlet (right), far-field (top/bottom)

  // Equilibrium population for direction q at density rho, velocity (ux, uy).
  static float equilibrium(int q, float rho, float ux, float uy);

  size_t cell(int x, int y) const { return static_cast<size_t>(y) * nx_ + x; }
  size_t idx(int q, int x, int y) const { return static_cast<size_t>(q) * nx_ * ny_ + cell(x, y); }

  int nx_, ny_;
  float u0_, viscosity_;
  long steps_ = 0;

  std::vector<float> f_;      // populations, Q * nx * ny
  std::vector<float> fTmp_;   // scratch buffer for streaming (swap with f_)
  std::vector<uint8_t> obstacle_;  // 1 = solid
  std::vector<float> rho_, ux_, uy_;
};
