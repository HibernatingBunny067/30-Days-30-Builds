#include "image.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>

namespace {

struct RGB { uint8_t r, g, b; };

uint8_t toByte(float v) { return static_cast<uint8_t>(std::clamp(v, 0.0f, 1.0f) * 255.0f + 0.5f); }

RGB diverging(float t) {  // t in [-1, 1]: blue -> white -> red
  t = std::clamp(t, -1.0f, 1.0f);
  return t < 0 ? RGB{toByte(1 + t), toByte(1 + 0.6f * t), 255}
               : RGB{255, toByte(1 - 0.6f * t), toByte(1 - t)};
}

RGB sequential(float t) {  // t in [0, 1]: black -> red -> yellow -> white
  t = std::clamp(t, 0.0f, 1.0f);
  return {toByte(3 * t), toByte(3 * t - 1), toByte(3 * t - 2)};
}

}  // namespace

bool writePPM(const std::string& path, const std::vector<float>& field,
              const std::vector<uint8_t>& obstacle, int nx, int ny, bool symmetric) {
  // Scale by the 99th percentile so a few extreme cells don't wash out the image.
  std::vector<float> mags;
  mags.reserve(field.size());
  for (size_t i = 0; i < field.size(); ++i)
    if (!obstacle[i] && std::isfinite(field[i])) mags.push_back(std::fabs(field[i]));
  float scale = 1e-6f;
  if (!mags.empty()) {
    auto p99 = mags.begin() + static_cast<long>(mags.size() * 0.99);
    std::nth_element(mags.begin(), p99, mags.end());
    scale = std::max(*p99, 1e-6f);
  }

  std::ofstream out(path, std::ios::binary);
  if (!out) return false;
  out << "P6\n" << nx << ' ' << ny << "\n255\n";
  for (size_t i = 0; i < field.size(); ++i) {
    RGB c = obstacle[i] ? RGB{40, 43, 51}
            : symmetric ? diverging(field[i] / scale)
                        : sequential(field[i] / scale);
    out.put(static_cast<char>(c.r)).put(static_cast<char>(c.g)).put(static_cast<char>(c.b));
  }
  return static_cast<bool>(out);
}
