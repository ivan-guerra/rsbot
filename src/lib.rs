use anyhow::{Context, Result};
use device_query::{DeviceQuery, DeviceState};
use kurbo::{CubicBez, ParamCurve, Point};
use log::debug;
use rand::random_range;
use serde::Deserialize;
use std::fs::File;
use std::io::BufReader;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant};

#[derive(Debug)]
pub struct BotConfig {
    pub script: PathBuf,
    pub runtime: u64,
    pub debug: bool,
}

#[derive(Debug, Deserialize)]
#[serde(tag = "type")]
enum BotEvent {
    #[serde(rename = "mouse")]
    Mouse {
        id: String,
        pos: [u32; 2],
        delay_rng: [u32; 2],
    },
    #[serde(rename = "keypress")]
    KeyPress {
        id: String,
        keycode: String,
        delay_rng: [u32; 2],
        count: u32,
    },
}

fn read_bot_script(path: &Path) -> Result<Vec<BotEvent>> {
    let file = File::open(path).context("Failed to open bot script")?;
    let reader = BufReader::new(file);
    let events: Vec<BotEvent> =
        serde_json::from_reader(reader).context("Failed to parse bot script")?;

    Ok(events)
}

fn run_xdotool(args: &[&str]) -> Result<()> {
    Command::new("xdotool")
        .args(args)
        .output()
        .context(format!("Failed to execute xdotool with args: {:?}", args))?;
    Ok(())
}

fn mouse_bez(init_pos: Point, fin_pos: Point) -> CubicBez {
    const MIN_DEVIATION: f64 = 30.0;

    let dx = fin_pos.x - init_pos.x;
    let dy = fin_pos.y - init_pos.y;
    let dist = (dx * dx + dy * dy).sqrt();

    let max_dev = dist * (MIN_DEVIATION / 50.0);
    let ctrl1_offset = random_range(max_dev * 0.5..=max_dev);
    let ctrl2_offset = random_range(max_dev * 0.3..=max_dev * 0.8);

    // Calculate control points with more natural curves
    let angle = dy.atan2(dx);
    let ctrl1_angle = angle + random_range(-0.8..0.8);
    let ctrl2_angle = angle + random_range(-0.5..0.5);

    let ctrl1 = Point::new(
        init_pos.x + ctrl1_offset * ctrl1_angle.cos(),
        init_pos.y + ctrl1_offset * ctrl1_angle.sin(),
    );
    let ctrl2 = Point::new(
        fin_pos.x - ctrl2_offset * ctrl2_angle.cos(),
        fin_pos.y - ctrl2_offset * ctrl2_angle.sin(),
    );

    CubicBez::new(init_pos, ctrl1, ctrl2, fin_pos)
}

fn move_mouse(target: Point) -> Result<()> {
    const MOUSE_SETTLE_DELAY_MS: u64 = 50;
    let start_pos = get_mouse_pos();
    let target_rand = Point::new(
        target.x + f64::from(random_range(-2..=2)),
        target.y + f64::from(random_range(-2..=2)),
    );
    let curve = mouse_bez(start_pos, target_rand);
    let points: Vec<Point> = (0..=100)
        .map(|t| f64::from(t) / 100.0)
        .map(|t| curve.eval(t))
        .collect();

    debug!(
        "Moving mouse from ({:.1}, {:.1}) to ({:.1}, {:.1})",
        start_pos.x, start_pos.y, target_rand.x, target_rand.y
    );
    for point in points {
        let x = point.x.round() as i32;
        let y = point.y.round() as i32;

        run_xdotool(&["mousemove", &x.to_string(), &y.to_string()]).context(format!(
            "Failed to execute xdotool for mouse move to ({}, {})",
            point.x, point.y
        ))?;
    }

    std::thread::sleep(Duration::from_millis(MOUSE_SETTLE_DELAY_MS));

    Ok(())
}

fn get_mouse_pos() -> Point {
    let device_state = DeviceState::new();
    let mouse_state = device_state.get_mouse();

    Point::new(mouse_state.coords.0.into(), mouse_state.coords.1.into())
}

fn left_click() -> Result<()> {
    run_xdotool(&["click", "1"]).context("Failed to execute xdotool for left click")?;
    Ok(())
}

fn shift_left_click() -> Result<()> {
    const SHIFT_DELAY_MS: u64 = 100;

    run_xdotool(&["keydown", "Shift"]).context("Failed to execute xdotool for Shift key down")?;
    std::thread::sleep(Duration::from_millis(SHIFT_DELAY_MS));

    run_xdotool(&["click", "1"]).context("Failed to execute xdotool for left click with Shift")?;
    std::thread::sleep(Duration::from_millis(SHIFT_DELAY_MS));

    run_xdotool(&["keyup", "Shift"]).context("Failed to execute xdotool for Shift key up")?;
    std::thread::sleep(Duration::from_millis(SHIFT_DELAY_MS));

    Ok(())
}

fn press_key(keycode: &str) -> Result<()> {
    const KEY_DELAY_MIN_MS: u64 = 100;
    const KEY_DELAY_MAX_MS: u64 = 150;

    run_xdotool(&["key", keycode])
        .context(format!("Failed to execute xdotool for key '{}'", keycode))?;

    std::thread::sleep(Duration::from_millis(random_range(
        KEY_DELAY_MIN_MS..=KEY_DELAY_MAX_MS,
    )));

    Ok(())
}

fn drop_special_log() -> Result<()> {
    const CTRL_DELAY_MS: u64 = 100;

    press_key("d")?;

    run_xdotool(&["keydown", "Control"])
        .context("Failed to execute xdotool for Control key down")?;
    std::thread::sleep(Duration::from_millis(CTRL_DELAY_MS));

    run_xdotool(&["key", "a"]).context("Failed to execute xdotool for 'a' key with Control")?;
    std::thread::sleep(Duration::from_millis(CTRL_DELAY_MS));

    run_xdotool(&["keyup", "Control"]).context("Failed to execute xdotool for Control key up")?;
    std::thread::sleep(Duration::from_millis(CTRL_DELAY_MS));

    Ok(())
}

fn drop_inventory() -> Result<()> {
    const INVENTORY_ROWS: usize = 7;
    const INVENTORY_COLS: usize = 4;
    const BASE_X: f64 = 780.0;
    const BASE_Y: f64 = 700.0;
    const COL_SPACING: f64 = 50.0;
    const ROW_SPACING: f64 = 37.0;

    for row in 0..INVENTORY_ROWS {
        for col in 0..INVENTORY_COLS {
            let x = BASE_X + col as f64 * COL_SPACING;
            let y = BASE_Y + row as f64 * ROW_SPACING;
            let inventory_pos = Point::new(x, y);

            move_mouse(inventory_pos)?;
            shift_left_click().context("Failed to perform Shift + Click for inventory drop")?;
        }
    }
    Ok(())
}

fn exec_event(event: &BotEvent) -> Result<()> {
    let sleep_random_delay = |delay_rng: &[u32; 2]| {
        let delay = random_range(delay_rng[0]..=delay_rng[1]);
        debug!("Sleeping for {} ms", delay);
        std::thread::sleep(Duration::from_millis(delay.into()));
    };

    match event {
        BotEvent::Mouse { id, pos, delay_rng } => {
            debug!("Executing mouse event '{}' at ({}, {})", id, pos[0], pos[1]);
            if id.contains("drop_inventory") {
                debug!("Dropping inventory");
                drop_inventory().context("Failed to drop inventory")?;
            } else {
                let point = Point::new(pos[0].into(), pos[1].into());

                move_mouse(point)?;
                left_click()?;
                sleep_random_delay(delay_rng);
            }
        }
        BotEvent::KeyPress {
            id,
            keycode,
            delay_rng,
            count,
        } => {
            debug!("Executing keypress '{}': '{}' x{}", id, keycode, count);

            for _ in 0..*count {
                press_key(keycode)?;
            }
            sleep_random_delay(delay_rng);
        }
    }
    Ok(())
}

pub fn run_event_loop(config: &BotConfig) -> Result<()> {
    let events = read_bot_script(&config.script)?;
    debug!("Loaded {} events from script", events.len());

    let runtime = Duration::from_secs(config.runtime);
    let start_time = Instant::now();
    let end_time = start_time + runtime;
    debug!("Starting event loop for {} seconds", config.runtime);

    let mut iteration = 0;
    while Instant::now() < end_time {
        debug!("Starting iteration {}", iteration);

        for event in &events {
            exec_event(event)?;
        }
        iteration += 1;

        if iteration % 2 == 0 {
            debug!("Performing special log drop after iteration {}", iteration);
            drop_special_log().context("Failed to drop special log")?;
        }
    }

    debug!("Event loop completed after {} iterations", iteration);
    Ok(())
}
