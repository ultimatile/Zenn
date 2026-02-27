// 例4: inherent impl でエラーになる最小例
//
// cargo build --example 04_inherent_error
// → E0592 エラーになることを確認

struct Tensor<T> {
    value: T,
}

// 同じ型 Tensor<i32> に同じメソッド double を2回定義
impl Tensor<i32> {
    fn double(&self) -> i32 {
        self.value * 2
    }
}

impl Tensor<i32> {
    fn double(&self) -> i32 {
        self.value * 2
    } // E0592エラー！
}

fn main() {}
