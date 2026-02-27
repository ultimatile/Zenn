// 例2: Extension trait パターン - コンパイルが通る
//
// cargo run --example 02_extension_trait

use num_complex::Complex;
use num_traits::Float;

struct Tensor<T> {
    data: Vec<T>,
}

impl<T> Tensor<T> {
    fn new(data: Vec<T>) -> Self {
        Tensor { data }
    }
}

// trait impl: traitを型に実装
// TensorExt<T> は型パラメータ T ごとに「別のtrait」として扱われる
trait TensorExt<T> {
    fn norm(&self) -> T;
}

impl<T: Float> TensorExt<T> for Tensor<T> {
    fn norm(&self) -> T {
        println!("  → TensorExt<T> for Tensor<T> (実数版)");
        self.data
            .iter()
            .fold(T::zero(), |acc, x| acc + *x * *x)
            .sqrt()
    }
}

impl<T: Float> TensorExt<T> for Tensor<Complex<T>> {
    fn norm(&self) -> T {
        println!("  → TensorExt<T> for Tensor<Complex<T>> (複素数版)");
        self.data
            .iter()
            .fold(T::zero(), |acc, x| acc + x.norm_sqr())
            .sqrt()
    }
}

fn main() {
    println!("=== Tensor<f64> の場合 ===");
    let real_tensor: Tensor<f64> = Tensor::new(vec![3.0, 4.0]);
    let n: f64 = real_tensor.norm();
    println!("結果: {}\n", n);

    println!("=== Tensor<Complex<f64>> の場合 ===");
    let complex_tensor: Tensor<Complex<f64>> = Tensor::new(vec![Complex::new(3.0, 4.0)]);
    let cn: f64 = complex_tensor.norm();
    println!("結果: {}\n", cn);
}
