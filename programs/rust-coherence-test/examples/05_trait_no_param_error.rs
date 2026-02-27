// 例5: 型パラメータなしのtraitだとエラーになる
//
// cargo build --example 05_trait_no_param_error
// → E0119 エラーになることを確認

use num_complex::Complex;
use num_traits::Float;

struct Tensor<T> {
    data: Vec<T>,
}

// 型パラメータ【なし】のtrait
trait TensorExt {
    type Output;
    fn norm(&self) -> Self::Output;
}

impl<T: Float> TensorExt for Tensor<T> {
    type Output = T;
    fn norm(&self) -> T {
        self.data
            .iter()
            .fold(T::zero(), |acc, x| acc + *x * *x)
            .sqrt()
    }
}

impl<T: Float> TensorExt for Tensor<Complex<T>> {
    type Output = T;
    fn norm(&self) -> T {
        self.data
            .iter()
            .fold(T::zero(), |acc, x| acc + x.norm_sqr())
            .sqrt()
    }
}
// ↑ E0119: TensorExt という「同じtrait」を Tensor<Complex<_>> に2回実装しようとしている

fn main() {}
