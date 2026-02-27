// coherence/orphan ルールのテスト用プロジェクト
//
// 各例は examples/ ディレクトリにあります:
//
// cargo build --example 01_original_problem     # E0592エラー
// cargo run --example 02_extension_trait        # OK
// cargo run --example 03_trait_vs_inherent      # trait vs inherent の違い
// cargo build --example 04_inherent_error       # E0592エラー
// cargo build --example 05_trait_no_param_error # E0119エラー
// cargo run --example 06_newtype                # OK
// cargo run --example 07_sealed                 # OK

fn main() {
    println!("examples/ ディレクトリの各例を実行してください");
    println!();
    println!("【動作する例】");
    println!("  cargo run --example 02_extension_trait");
    println!("  cargo run --example 03_trait_vs_inherent");
    println!("  cargo run --example 06_newtype");
    println!("  cargo run --example 07_sealed");
    println!();
    println!("【エラーになる例】");
    println!("  cargo build --example 01_original_problem");
    println!("  cargo build --example 04_inherent_error");
    println!("  cargo build --example 05_trait_no_param_error");
}
