// 例3: trait impl vs inherent impl の違い
//
// cargo run --example 03_trait_vs_inherent

struct Tensor<T> {
    value: T,
}

// ============================================================
// 【inherent impl】型に直接メソッドを定義
// ============================================================
// 以下はコンパイルエラーになる（コメントアウト）：
//
// impl Tensor<i32> {
//     fn double(&self) -> i32 { self.value * 2 }
// }
// impl Tensor<i32> {
//     fn double(&self) -> i32 { self.value * 2 }  // E0592: 同じ型に同じメソッド！
// }

// ============================================================
// 【trait impl】traitを型に実装
// ============================================================
// Doubler<T> は「trait」- T ごとに別のtraitになる
trait Doubler<T> {
    fn double(&self) -> T;
}

// Doubler<i32> を Tensor<i32> に実装
impl Doubler<i32> for Tensor<i32> {
    fn double(&self) -> i32 {
        println!("  Doubler<i32>::double が呼ばれた");
        self.value * 2
    }
}

// Doubler<i64> を Tensor<i32> に実装
// これは Doubler<i32> とは【別のtrait】なのでOK！
impl Doubler<i64> for Tensor<i32> {
    fn double(&self) -> i64 {
        println!("  Doubler<i64>::double が呼ばれた");
        (self.value * 2) as i64
    }
}

fn main() {
    let t = Tensor { value: 5_i32 };

    println!("=== Tensor<i32> は2つの異なるtraitを実装できる ===\n");

    // Doubler<i32>::double を呼ぶ
    let result1: i32 = Doubler::<i32>::double(&t);
    println!("結果 (i32): {}\n", result1);

    // Doubler<i64>::double を呼ぶ
    let result2: i64 = Doubler::<i64>::double(&t);
    println!("結果 (i64): {}\n", result2);

    println!("=== ポイント ===");
    println!("- Doubler<i32> と Doubler<i64> は【別のtrait】");
    println!("- 同じ型が複数の異なるtraitを実装しても問題ない");
    println!("- Vec<T> が Clone も Debug も実装できるのと同じ原理");
}
