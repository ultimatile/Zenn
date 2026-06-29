use foo::{Sector, Thing};

pub fn make<S: Sector>() -> Thing<S> {
    Thing(core::marker::PhantomData)
}
