use anyhow::{Context, Result};
use clap::Parser;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    #[arg(help = "path to bot script")]
    script: std::path::PathBuf,

    #[arg(
        short = 'r',
        long,
        default_value_t = 3600,
        help = "script runtime in seconds"
    )]
    runtime: u64,

    #[arg(short = 'g', long, default_value_t = false, help = "enable logging")]
    debug: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();
    let config = colorbot::BotConfig {
        script: args.script,
        runtime: args.runtime,
        debug: args.debug,
    };

    if config.debug {
        simplelog::TermLogger::init(
            simplelog::LevelFilter::Debug,
            simplelog::Config::default(),
            simplelog::TerminalMode::Mixed,
            simplelog::ColorChoice::Auto,
        )
        .context("Failed to initialize logger")?;
    }

    colorbot::run_event_loop(&config).context("Failed to run event loop")?;

    Ok(())
}
