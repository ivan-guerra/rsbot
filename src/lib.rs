use anyhow::{Context, Result};
use device_query::{DeviceQuery, DeviceState};
use enigo::{Button, Coordinate, Direction, Enigo, Key, Keyboard, Mouse, Settings};
use kurbo::{CubicBez, ParamCurve, Point};
use log::debug;
use rand::random_range;
use serde::Deserialize;
use std::fs::File;
use std::io::BufReader;
use std::path::{Path, PathBuf};
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
        keycode: char,
        delay_rng: [u32; 2],
        count: u32,
    },
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

fn move_mouse(enigo: &mut Enigo, target: Point) -> Result<()> {
    const MOUSE_SPEED: u32 = 64;
    let start_pos = get_mouse_pos();
    debug!(
        "Moving mouse from ({:.1}, {:.1}) to ({:.1}, {:.1})",
        start_pos.x, start_pos.y, target.x, target.y
    );
    let curve = mouse_bez(start_pos, target);
    let points: Vec<Point> = (0..=MOUSE_SPEED * 100)
        .map(|t| f64::from(t) / (f64::from(MOUSE_SPEED) * 100.0))
        .map(|t| curve.eval(t))
        .collect();

    for point in points {
        enigo
            .move_mouse(point.x as i32, point.y as i32, Coordinate::Abs)
            .context(format!(
                "Failed to move mouse to ({}, {})",
                point.x, point.y
            ))?;
    }
    Ok(())
}

fn read_bot_script(path: &Path) -> Result<Vec<BotEvent>> {
    let file = File::open(path).context("Failed to open bot script")?;
    let reader = BufReader::new(file);
    let events: Vec<BotEvent> =
        serde_json::from_reader(reader).context("Failed to parse bot script")?;

    Ok(events)
}

fn get_mouse_pos() -> Point {
    let device_state = DeviceState::new();
    let mouse_state = device_state.get_mouse();

    Point::new(mouse_state.coords.0.into(), mouse_state.coords.1.into())
}

fn left_click(target: Point) -> Result<()> {
    let mut enigo = Enigo::new(&Settings::default()).context("Failed to init enigo")?;
    let target_rand = Point::new(
        target.x + f64::from(random_range(-5..=5)),
        target.y + f64::from(random_range(-5..=5)),
    );
    debug!(
        "Clicking at ({:.1}, {:.1}) with random offset",
        target_rand.x, target_rand.y
    );

    move_mouse(&mut enigo, target_rand).context("Failed to move mouse to click location")?;
    enigo
        .button(Button::Left, Direction::Click)
        .context("Failed to left click")?;
    Ok(())
}

fn press_key(keycode: char) -> Result<()> {
    let mut enigo = Enigo::new(&Settings::default()).context("Failed to init enigo")?;

    enigo
        .key(Key::Unicode(keycode), Direction::Click)
        .context(format!("Failed to press key {}", keycode))?;
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
            let point = Point::new(pos[0].into(), pos[1].into());

            left_click(point)?;
            sleep_random_delay(delay_rng);
        }
        BotEvent::KeyPress {
            id,
            keycode,
            delay_rng,
            count,
        } => {
            debug!("Executing keypress '{}': '{}' x{}", id, keycode, count);

            for _ in 0..*count {
                press_key(*keycode)?;

                // Simulate natural keypress timing
                let key_delay_ms = Duration::from_millis(random_range(100..=300));
                std::thread::sleep(key_delay_ms);
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
    }

    debug!("Event loop completed after {} iterations", iteration);
    Ok(())
}
