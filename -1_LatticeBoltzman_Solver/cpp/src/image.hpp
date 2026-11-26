#pragma once
#include <cstdint>
#include <string>
#include <vector>

// Writes a binary PPM (P6) image of a scalar field. Obstacles are drawn grey.
// symmetric = true colours [-max, max] blue-white-red (vorticity);
// false colours [0, max] black-to-yellow (speed).
// PPM opens in macOS Preview; convert to PNG/GIF/MP4 with ffmpeg for posting.
bool writePPM(const std::string& path, const std::vector<float>& field,
              const std::vector<uint8_t>& obstacle, int nx, int ny, bool symmetric);
