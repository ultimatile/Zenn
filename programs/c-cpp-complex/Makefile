# Compiler options
CXX := g++-13
CLANGXX := clang++
ICPC := icpc
CXXFLAGS := -Wall -Wextra

# Source file
SOURCE := complex.cpp

# Output binaries
OUT_GPP := main_gpp
OUT_GPP_11 := main_gpp_c++11
OUT_GPP_14 := main_gpp_c++14
OUT_GPP_17 := main_gpp_c++17
OUT_GPP_20 := main_gpp_c++20

OUT_CLANG := main_clang
OUT_CLANG_11 := main_clang_c++11
OUT_CLANG_14 := main_clang_c++14
OUT_CLANG_17 := main_clang_c++17
OUT_CLANG_20 := main_clang_c++20

OUT_ICPC := main_icpc
OUT_ICPC_11 := main_icpc_c++11
OUT_ICPC_14 := main_icpc_c++14
OUT_ICPC_17 := main_icpc_c++17
OUT_ICPC_20 := main_icpc_c++20

# Error message files
ERRORS_GPP := errors_gpp.txt
ERRORS_GPP_11 := errors_gpp_c++11.txt
ERRORS_GPP_14 := errors_gpp_c++14.txt
ERRORS_GPP_17 := errors_gpp_c++17.txt
ERRORS_GPP_20 := errors_gpp_c++20.txt

ERRORS_CLANG := errors_clang.txt
ERRORS_CLANG_11 := errors_clang_c++11.txt
ERRORS_CLANG_14 := errors_clang_c++14.txt
ERRORS_CLANG_17 := errors_clang_c++17.txt
ERRORS_CLANG_20 := errors_clang_c++20.txt

ERRORS_ICPC := errors_icpc.txt
ERRORS_ICPC_11 := errors_icpc_c++11.txt
ERRORS_ICPC_14 := errors_icpc_c++14.txt
ERRORS_ICPC_17 := errors_icpc_c++17.txt
ERRORS_ICPC_20 := errors_icpc_c++20.txt

.PHONY: all clean

all: $(OUT_GPP) $(OUT_GPP_11) $(OUT_GPP_14) $(OUT_GPP_17) $(OUT_GPP_20) \
     $(OUT_CLANG) $(OUT_CLANG_11) $(OUT_CLANG_14) $(OUT_CLANG_17) $(OUT_CLANG_20) \
     $(OUT_ICPC) $(OUT_ICPC_11) $(OUT_ICPC_14) $(OUT_ICPC_17) $(OUT_ICPC_20)

$(OUT_GPP): $(SOURCE)
	$(CXX) $(CXXFLAGS) $< -o $@ 2> $(ERRORS_GPP) || true

$(OUT_GPP_11): $(SOURCE)
	$(CXX) $(CXXFLAGS) -std=c++11 $< -o $@ 2> $(ERRORS_GPP_11) || true

$(OUT_GPP_14): $(SOURCE)
	$(CXX) $(CXXFLAGS) -std=c++14 $< -o $@ 2> $(ERRORS_GPP_14) || true

$(OUT_GPP_17): $(SOURCE)
	$(CXX) $(CXXFLAGS) -std=c++17 $< -o $@ 2> $(ERRORS_GPP_17) || true

$(OUT_GPP_20): $(SOURCE)
	$(CXX) $(CXXFLAGS) -std=c++20 $< -o $@ 2> $(ERRORS_GPP_20) || true

$(OUT_CLANG): $(SOURCE)
	$(CLANGXX) $(CXXFLAGS) $< -o $@ 2> $(ERRORS_CLANG) || true

$(OUT_CLANG_11): $(SOURCE)
	$(CLANGXX) $(CXXFLAGS) -std=c++11 $< -o $@ 2> $(ERRORS_CLANG_11) || true

$(OUT_CLANG_14): $(SOURCE)
	$(CLANGXX) $(CXXFLAGS) -std=c++14 $< -o $@ 2> $(ERRORS_CLANG_14) || true

$(OUT_CLANG_17): $(SOURCE)
	$(CLANGXX) $(CXXFLAGS) -std=c++17 $< -o $@ 2> $(ERRORS_CLANG_17) || true

$(OUT_CLANG_20): $(SOURCE)
	$(CLANGXX) $(CXXFLAGS) -std=c++20 $< -o $@ 2> $(ERRORS_CLANG_20) || true

$(OUT_ICPC): $(SOURCE)
	$(ICPC) $(CXXFLAGS) $< -o $@ 2> $(ERRORS_ICPC) || true

$(OUT_ICPC_11): $(SOURCE)
	$(ICPC) $(CXXFLAGS) -std=c++11 $< -o $@ 2> $(ERRORS_ICPC_11) || true

$(OUT_ICPC_14): $(SOURCE)
	$(ICPC) $(CXXFLAGS) -std=c++14 $< -o $@ 2> $(ERRORS_ICPC_14) || true

$(OUT_ICPC_17): $(SOURCE)
	$(ICPC) $(CXXFLAGS) -std=c++17 $< -o $@ 2> $(ERRORS_ICPC_17) || true

$(OUT_ICPC_20): $(SOURCE)
	$(ICPC) $(CXXFLAGS) -std=c++20 $< -o $@ 2> $(ERRORS_ICPC_20) || true

clean:
	rm -f $(OUT_GPP) $(OUT_GPP_11) $(OUT_GPP_14) $(OUT_GPP_17) $(OUT_GPP_20) \
	      $(OUT_CLANG) $(OUT_CLANG_11) $(OUT_CLANG_14) $(OUT_CLANG_17) $(OUT_CLANG_20) \
	      $(OUT_ICPC) $(OUT_ICPC_11) $(OUT_ICPC_14) $(OUT_ICPC_17) $(OUT_ICPC_20) \
	      $(ERRORS_GPP) $(ERRORS_GPP_11) $(ERRORS_GPP_14) $(ERRORS_GPP_17) $(ERRORS_GPP_20) \
	      $(ERRORS_CLANG) $(ERRORS_CLANG_11) $(ERRORS_CLANG_14) $(ERRORS_CLANG_17) $(ERRORS_CLANG_20) \
	      $(ERRORS_ICPC) $(ERRORS_ICPC_11) $(ERRORS_ICPC_14) $(ERRORS_ICPC_17) $(ERRORS_ICPC_20)
