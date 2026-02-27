// 例1: 元の問題 - E0592エラーになるコード
//
// cargo build --example 01_original_problem
// → エラーになることを確認

use num_complex::Complex;
use num_traits::Float;

struct Tensor<T> {
    data: Vec<T>,
}

// inherent impl: 型に直接メソッドを定義
impl<T: Float> Tensor<T> {
    fn norm(&self) -> T {
        // 実数用の実装
        self.data
            .iter()
            .fold(T::zero(), |acc, x| acc + *x * *x)
            .sqrt()
    }
}

impl<T: Float> Tensor<Complex<T>> {
    fn norm(&self) -> T {
        // 複素数用の実装
        self.data
            .iter()
            .fold(T::zero(), |acc, x| acc + x.norm_sqr())
            .sqrt()
    }
}

fn main() {
    println!("このコードはコンパイルエラーになります");
}
