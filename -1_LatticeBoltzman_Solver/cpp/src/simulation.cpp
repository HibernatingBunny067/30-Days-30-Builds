#include "simulation.hpp"

#include <cmath>

using namespace lattice;

Simulation::Simulation(int nx, int ny, float u0, float viscosity)
    : nx_(nx), ny_(ny), u0_(u0), viscosity_(viscosity),
      f_(static_cast<size_t>(Q) * nx * ny), fTmp_(f_.size()),
      obstacle_(static_cast<size_t>(nx) * ny, 0),
      rho_(obstacle_.size()), ux_(obstacle_.size()), uy_(obstacle_.size()) {
  reset();
}

void Simulation::addCylinder(float cx, float cy, float radius) {
  for (int y = 0; y < ny_; ++y)
    for (int x = 2; x < nx_ - 2; ++x)  // keep inlet/outlet columns open
      if ((x - cx) * (x - cx) + (y - cy) * (y - cy) <= radius * radius) obstacle_[cell(x, y)] = 1;
  reset();
}

void Simulation::reset() {
  for (int y = 0; y < ny_; ++y)
    for (int x = 0; x < nx_; ++x) {
      float u = obstacle_[cell(x, y)] ? 0.0f : u0_;
      for (int q = 0; q < Q; ++q) f_[idx(q, x, y)] = equilibrium(q, 1.0f, u, 0.0f);
    }
  steps_ = 0;
  computeMacroscopic();
}

void Simulation::step() {
  computeMacroscopic();
  collide();
  stream();
  bounceBack();
  applyBoundaries();
  ++steps_;
}

bool Simulation::isFinite() const {
  for (float v : f_)
    if (!std::isfinite(v)) return false;
  return true;
}

void Simulation::computeMacroscopic() {
  // Density = sum of populations; velocity = momentum / density.
  for (int y = 0; y < ny_; ++y)
    for (int x = 0; x < nx_; ++x) {
      float rho = 0, mx = 0, my = 0;
      for (int q = 0; q < Q; ++q) {
        float fq = f_[idx(q, x, y)];
        rho += fq;
        mx += fq * ex[q];
        my += fq * ey[q];
      }
      size_t c = cell(x, y);
      rho_[c] = rho;
      ux_[c] = rho > 0 ? mx / rho : 0;
      uy_[c] = rho > 0 ? my / rho : 0;
    }
}

std::vector<float> Simulation::vorticity() const {
  // Curl of velocity with central differences: d(uy)/dx - d(ux)/dy.
  std::vector<float> w(rho_.size(), 0.0f);
  for (int y = 1; y < ny_ - 1; ++y)
    for (int x = 1; x < nx_ - 1; ++x) {
      if (obstacle_[cell(x, y)]) continue;
      w[cell(x, y)] = 0.5f * ((uy_[cell(x + 1, y)] - uy_[cell(x - 1, y)]) -
                              (ux_[cell(x, y + 1)] - ux_[cell(x, y - 1)]));
    }
  return w;
}

std::vector<float> Simulation::speed() const {
  std::vector<float> s(rho_.size());
  for (size_t c = 0; c < s.size(); ++c)
    s[c] = obstacle_[c] ? 0.0f : std::sqrt(ux_[c] * ux_[c] + uy_[c] * uy_[c]);
  return s;
}

// ---------------------------------------------------------------------------
// Your part. Implement these in order, checking each against the Python
// version (python/solver/lbm.py) before moving on.
// ---------------------------------------------------------------------------

float Simulation::equilibrium(int q, float rho, float ux, float uy) {
  // TODO (week 2): second-order Maxwell-Boltzmann equilibrium
  //   cu  = 3 (e_q . u)
  //   feq = w_q * rho * (1 + cu + cu^2 / 2 - 1.5 |u|^2)
  // Placeholder: fluid at rest (ignores ux, uy), so the program still runs.
  (void)ux;
  (void)uy;
  return w[q] * rho;
}

void Simulation::collide() {
  // TODO (week 3): for every fluid cell and direction q,
  //   f[q] += omega() * (equilibrium(q, rho, ux, uy) - f[q])
  // Skip obstacle cells: they hold bounced-back populations.
}

void Simulation::stream() {
  // TODO (week 3): copy each population into its neighbour:
  //   fTmp_[idx(q, x + ex[q], y + ey[q])] = f_[idx(q, x, y)]
  // wrapping around the edges (periodic), then std::swap(f_, fTmp_).
}

void Simulation::bounceBack() {
  // TODO (week 4): in every obstacle cell, swap each population with its
  // opposite direction (f[q] <-> f[opposite[q]]) so it streams back out.
}

void Simulation::applyBoundaries() {
  // TODO (week 4):
  //   - outlet (x = nx-1): copy every population from column nx-2
  //   - inlet (x = 0) and top/bottom rows: set to equilibrium(q, 1, u0_, 0)
}
