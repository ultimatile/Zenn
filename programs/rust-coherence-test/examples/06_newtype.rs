// 例6: Newtype パターン
//
// cargo run --example 06_newtype

use num_complex::Complex;
use num_traits::Float;

// Real<T> と Cplx<T> は完全に別の型
struct Real<T>(T);
struct Cplx<T>(Complex<T>);

impl<T: Float> Real<T> {
    fn norm(&self) -> T {
        println!("  Real::norm が呼ばれた");
        self.0.abs()
    }
}

impl<T: Float> Cplx<T> {
    fn norm(&self) -> T {
        println!("  Cplx::norm が呼ばれた");
        self.0.norm()
    }
}

fn main() {
    println!("=== Newtype パターン ===\n");

    let r = Real(3.0_f64);
    println!("Real(3.0).norm() = {}\n", r.norm());

    let c = Cplx(Complex::new(3.0_f64, 4.0));
    println!("Cplx(3+4i).norm() = {}\n", c.norm());

    println!("=== ポイント ===");
    println!("- Real<T> と Cplx<T> は完全に別の型");
    println!("- コンパイラにとって重複の可能性がない");
}
