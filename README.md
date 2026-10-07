# Park Hopper

One day, four parks, four rides, and Mickey waiting in front of Cinderella
Castle. An Atari 2600 style side-scroller set at Walt Disney World, running
entirely inside your terminal.

<p align="center">
<img width="688" height="572" alt="park_hopper" src="https://github.com/user-attachments/assets/75475756-83d8-491c-8cbe-5a71c83b7d17" />
<p>

```bash
./play.sh
```

or `python3 -m hopper` from this folder. Needs Python 3 (ships with macOS) and
a terminal at least 80 columns by 24 rows. A 256-colour terminal gives the
proper cartridge palette; 8-colour terminals still work. Hold a key to keep
walking; a fast key-repeat rate in your OS settings makes it smoother.

## The game

You wake up at the Starlight Resort at 9:00 AM. The parks close at 9:00 PM.
Before then you need to ride one ride in each park, in any order, then get
back to Magic Kingdom and find Mickey in front of the castle.

| Park | Ride | Icon |
| --- | --- | --- |
| Magic Kingdom | Space Mountain | ▲ |
| Epcot | Guardians of the Galaxy: Cosmic Rewind | ● |
| Hollywood Studios | Mickey & Minnie's Runaway Railway | ★ |
| Animal Kingdom | Expedition Everest | ♣ |

- **MagicBand.** Grab it by your room door before you leave. The park gates
  flash blue and turn you away without it.
- **Buses.** Every place has a bus loop with a departure board and numbered
  bays. Each bay's bus shows its destination on the LED sign, and the bay
  layout is shuffled every game. Some bays go to Disney Springs, your resort or
  a water park, which cost you time. Stand at a bus door and press UP.
- **Navigating the roads.** On the bus you are the navigator. Three purple
  road signs scroll toward you; press LEFT or RIGHT for the exit that leads to
  your destination before the sign reaches the bus. The first sign lists
  places by name, the second groups them ("ALL THEME PARKS", "WATER PARKS"),
  the third shows only park symbols. A wrong or missed exit loops you around
  and costs eight minutes.
- **Magic Kingdom.** Jump the Main Street trolley, pass the castle, then climb
  the stairs to the PeopleMover station and ride a car over the Tomorrowland
  Speedway to Space Mountain. The Speedway is full of race cars if you try to
  walk it.
- **Epcot.** Walk under Spaceship Earth to Cosmic Rewind. It is virtual queue
  only: the Cast Member shows you three flags. Walk World Showcase and stamp
  your passport at the pavilions flying those flags, in that order. The wrong
  pavilion smudges the passport and you start over.
- **Hollywood Studios.** Goofy's train has jumped the track and all five
  railway signals must be green. Yellow switch levers stand along Hollywood
  Boulevard, Sunset Boulevard and into Galaxy's Edge. Each lever flips its own
  signal and its neighbours, so pick your combination. Stormtroopers patrol
  Galaxy's Edge; time your jumps.
- **Animal Kingdom.** Past the Tree of Life the trail turns Pitfall: jump the
  Kali River gaps, hop the rolling logs, and cross the crocodile pit on the
  crocs' backs while their mouths are shut. Everest is at the far end and the
  Yeti peeks out now and then.
- **The finale.** With all four icons lit, bus back to Magic Kingdom. Mickey is
  in front of Cinderella Castle. Press UP next to him for fireworks.
- **Time.** Walking costs about one park minute per 1.3 seconds. Buses cost
  six minutes a fork, rides twelve, bumps two, splashes three. If the clock
  hits 9:00 PM the park closes and it is game over. Minutes left when you
  meet Mickey are worth five points each.

The high score is saved to `highscore.json` in this folder.

## Controls

| Key | Action |
| --- | --- |
| Left / Right (or A / D) | Walk |
| Space (or Z) | Jump |
| Up / Enter (or E) | Use: board a bus, ride, talk, pull a lever, stamp a passport |
| Left / Right on the bus | Pick the exit |
| P | Pause |
| ? | How to play |
| Q / Esc | Quit (asks first) |

## Layout

```
hopper/
  constants.py   layout, timing, palette, block font, ride table, all sprite art
  world.py       the six scenes: resort, four parks, Disney Springs, and bus loops
  entities.py    trolley, race cars, logs, crocodiles, PeopleMover, stormtroopers
  engine.py      game loop, input, platform physics, bus trips, puzzles, rides
  render.py      curses drawing: HUD, scenes, bus signs, ride cutscenes, finale
  __main__.py    entry point
highscore.json   created after your first game
```

The ride names live in the `RIDES` table at the top of `constants.py`. The bay
spacing, gate position and each park's props are laid out in `world.py`; every
landmark is a small block-letter sprite in `constants.py`, so redrawing the
castle or adding a pavilion is a matter of editing a few strings.
