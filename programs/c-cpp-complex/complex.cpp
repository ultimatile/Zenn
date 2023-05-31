#include <complex>
#include <iostream>
int main ()
{
    std::complex<double> c1(1.0, 2.0);
    std::complex<double> c2(3.0, 4.0);
    std::cout << c1 + c2 << std::endl;
    float _Complex c3 = 1.0 + 2.0j;
    float _Complex c4 = 2.0 + 4.0j;
    std::cout << __real__ (c3 + c4) << "+" << __imag__ (c3 + c4) << "i" << std::endl;
    return 0;
}