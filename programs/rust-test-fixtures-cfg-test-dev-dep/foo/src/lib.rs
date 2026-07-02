pub struct Thing(pub i32);

pub fn consume(_t: Thing) {}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        let t = fixtures::make(); // fixtures経由でfooの型を作り
        consume(t);               // foo自身の関数へ戻す
    }
}
