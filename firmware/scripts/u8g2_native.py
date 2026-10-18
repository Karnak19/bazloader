# Native env only: builds U8g2's C core (src/clib, no Arduino in it) next to the logic, so the
# screen drawing in src/screen_draw.cpp renders to a real 128x64 buffer in the host tests.
# The library itself is in lib_ignore: its C++ wrapper (U8g2lib.cpp) needs Arduino.h.
import os

Import("env")

libdeps = os.path.join(env.subst("$PROJECT_LIBDEPS_DIR"), env.subst("$PIOENV"))
src = os.path.join(libdeps, "U8g2", "src")
if not os.path.isdir(src):
    raise RuntimeError("U8g2 not installed in %s: check lib_deps in [env:native]" % libdeps)
env.Append(CPPPATH=[src])
env.BuildSources(os.path.join("$BUILD_DIR", "u8g2"), os.path.join(src, "clib"))
