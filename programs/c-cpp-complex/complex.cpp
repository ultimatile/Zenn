#include <complex>
#include <iostream>
int main ()
{
    //std::complex<double> c1(1.0, 2.0);
    //std::complex<double> c2(3.0, 4.0);
    //std::cout << c1 + c2 << std::endl;
    //float _Complex c3 = 1.0 + 2.0j;
    //float _Complex c4 = 2.0 + 4.0j;
    //long double _Complex c5;
    //_Imaginary long double c6;
    //_Complex double z = 12.0 + 24.0i;
    //using namespace std::literals::complex_literals;
    //std::complex<double> w = 14.0 + 42.0i;
    //std::cout << __real__ (c3 + c4) << "+" << __imag__ (c3 + c4) << "i" << std::endl;
    //std::cout << __real__ z << "+" << __imag__ z << "i" << std::endl;
    //std::cout << w.real() << "+" << w.imag() << "i" << std::endl;
    _Complex double v = 12.0 + 24.0i;
    //_Complex double* p_v = &v;
    std::cout << __real__ v << "+" << __imag__ v << "i" << std::endl;
    std::cout << *v << "+" << *v + 1 << "i" << std::endl;
    return 0;
}