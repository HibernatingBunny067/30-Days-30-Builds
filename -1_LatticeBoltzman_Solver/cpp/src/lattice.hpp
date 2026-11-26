#pragma once
// D2Q9 lattice constants. Same ordering as python/solver/lbm.py so results can
// be compared direction by direction.
//
//   6   2   5        index: 0 rest, 1 E, 2 S, 3 W, 4 N, 5 SE, 6 SW, 7 NW, 8 NE
//     \ | /          (y grows downward: row 0 is the top of the image)
//   3 - 0 - 1
//     / | \
//   7   4   8
#include <array>

namespace lattice {

constexpr int Q = 9;
constexpr std::array<int, Q> ex = {0, 1, 0, -1, 0, 1, -1, -1, 1};
constexpr std::array<int, Q> ey = {0, 0, 1, 0, -1, 1, 1, -1, -1};
constexpr std::array<int, Q> opposite = {0, 3, 4, 1, 2, 7, 8, 5, 6};
constexpr std::array<float, Q> w = {4.f / 9,  1.f / 9,  1.f / 9,  1.f / 9, 1.f / 9,
                                    1.f / 36, 1.f / 36, 1.f / 36, 1.f / 36};

}  // namespace lattice
