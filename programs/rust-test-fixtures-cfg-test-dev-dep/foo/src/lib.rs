pub trait Sector {}
pub struct U1;
impl Sector for U1 {}

pub struct Thing<S: Sector>(pub core::marker::PhantomData<S>);

pub fn consume<S: Sector>(_t: Thing<S>) {}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn round_trip() {
        let t = fixtures::make::<U1>();
        consume(t);
    }
}
