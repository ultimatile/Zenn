#[derive(thiserror::Error, Debug)]
enum LeafError {
    #[error("file not found: {0}")]
    NotFound(String),
}

#[derive(thiserror::Error, Debug)]
enum MidSchoolA {
    #[error("backend operation failed")]
    Backend(#[from] LeafError),
}

#[derive(thiserror::Error, Debug)]
enum TopSchoolA {
    #[error("request handling failed")]
    Mid(#[from] MidSchoolA),
}

#[derive(thiserror::Error, Debug)]
enum MidSchoolB {
    #[error("backend operation failed: {0}")]
    Backend(#[from] LeafError),
}

#[derive(thiserror::Error, Debug)]
enum TopSchoolB {
    #[error("request handling failed: {0}")]
    Mid(#[from] MidSchoolB),
}

#[derive(thiserror::Error, Debug)]
enum TopTransparent {
    #[error(transparent)]
    Mid(#[from] MidSchoolB),
}

fn main() {
    print_case("School A: Display does not interpolate source", || {
        TopSchoolA::from(MidSchoolA::from(leaf()))
    });
    print_case("School B: every layer interpolates source", || {
        TopSchoolB::from(MidSchoolB::from(leaf()))
    });
    print_case("Transparent top wrapper over School B mid layer", || {
        TopTransparent::from(MidSchoolB::from(leaf()))
    });
}

fn leaf() -> LeafError {
    LeafError::NotFound("foo.txt".to_owned())
}

fn print_case<E, F>(title: &str, make_error: F)
where
    F: Fn() -> E,
    E: std::error::Error + Send + Sync + 'static,
{
    println!("== {title} ==");

    let error = anyhow::Error::new(make_error());
    println!("anyhow Display:");
    println!("{error}");
    println!();
    println!("anyhow alternate Display:");
    println!("{error:#}");
    println!();
    println!("anyhow Debug:");
    println!("{error:?}");
    println!();

    let error = eyre::Report::new(make_error());
    println!("eyre Display:");
    println!("{error}");
    println!();
    println!("eyre alternate Display:");
    println!("{error:#}");
    println!();
    println!("eyre Debug:");
    println!("{error:?}");
    println!();
}
