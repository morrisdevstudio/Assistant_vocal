fn main() {
    // The upstream Windows ORT 1.22 static package includes DML objects even
    // though our sessions explicitly select CPUExecutionProvider only.
    if std::env::var("CARGO_CFG_TARGET_OS").as_deref() == Ok("windows") {
        println!("cargo:rustc-link-lib=DXCORE");
        println!("cargo:rustc-link-lib=DirectML");
    }
}
