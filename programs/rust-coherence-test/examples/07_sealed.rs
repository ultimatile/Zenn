// 例7: Sealed trait パターン
//
// cargo run --example 07_sealed

use num_complex::Complex;
use num_traits::Float;

mod sealed {
    pub trait Sealed {}
    impl Sealed for f32 {}
    impl Sealed for f64 {}
    impl Sealed for num_complex::Complex<f32> {}
    impl Sealed for num_complex::Complex<f64> {}
}

pub trait Scalar: sealed::Sealed + Clone + Copy {
    type Real;
    fn abs(self) -> Self::Real;
    fn conj(self) -> Self;
}

impl Scalar for f32 {
    type Real = f32;
    fn abs(self) -> f32 {
        println!("  Scalar for f32::abs");
        f32::abs(self)
    }
    fn conj(self) -> f32 {
        self
    }
}

impl Scalar for f64 {
    type Real = f64;
    fn abs(self) -> f64 {
        println!("  Scalar for f64::abs");
        f64::abs(self)
    }
    fn conj(self) -> f64 {
        self
    }
}

impl Scalar for Complex<f32> {
    type Real = f32;
    fn abs(self) -> f32 {
        println!("  Scalar for Complex<f32>::abs");
        self.norm()
    }
    fn conj(self) -> Complex<f32> {
        Complex::conj(&self)
    }
}

impl Scalar for Complex<f64> {
    type Real = f64;
    fn abs(self) -> f64 {
        println!("  Scalar for Complex<f64>::abs");
        self.norm()
    }
    fn conj(self) -> Complex<f64> {
        Complex::conj(&self)
    }
}

struct Tensor<T> {
    data: Vec<T>,
}

impl<T: Scalar> Tensor<T> {
    fn new(data: Vec<T>) -> Self {
        Tensor { data }
    }

    fn norm(&self) -> T::Real
    where
        T::Real: std::iter::Sum + Float,
    {
        self.data
            .iter()
            .map(|x| x.abs() * x.abs())
            .sum::<T::Real>()
            .sqrt()
    }
}

fn main() {
    println!("=== Sealed trait パターン ===\n");

    let real_tensor: Tensor<f64> = Tensor::new(vec![3.0, 4.0]);
    println!("Tensor<f64>.norm() = {}\n", real_tensor.norm());

    let complex_tensor: Tensor<Complex<f64>> = Tensor::new(vec![Complex::new(3.0, 4.0)]);
    println!("Tensor<Complex<f64>>.norm() = {}\n", complex_tensor.norm());

    println!("=== ポイント ===");
    println!("- 具体的な型 (f32, f64, Complex<f32>, Complex<f64>) に個別impl");
    println!("- ジェネリックな impl<T: Float> を使わない");
    println!("- 「将来 Complex<U>: Float が追加されたら...」という問題が発生しない");
}
