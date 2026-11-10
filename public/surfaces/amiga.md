---
title: vAmigaWeb Amiga emulator iPad iPhone
description: cycle exact Amiga emulator in html5 / javascript. This Amiga emulator is compatible to the progressive-web-app (PWA) standard.
canonical: https://a2uicatalog.ai/surfaces/amiga/
generated_by: gen_page_twins.py
---

# vAmigaWeb Amiga emulator iPad iPhone

**booting into vAmigaWeb ...**

Downloading...

overview

bitplanes  auto-select

memory   live $px

What am I looking at?

On the left is an overview of the Amiga's configured RAM areas, with detected bitplanes shown underneath. On the right is the detail memory view, showing the currently selected memory window.

Drag or scroll to move through memory, type an address in the $ field to jump, or select a bitplane from the list to inspect it in the detail view.

###### Bitplane detection

The bitplanes panel **continuously tries to work out which memory areas are currently used as bitplanes** by watching the Amiga's DMA and measuring the line-to-line stride. Detected areas are listed on the left, largest first. Graphics in chip RAM show up as recognizable images.

With **auto-select** enabled, the detail view **automatically follows bitplane 1**: whenever the guessed bpl1 area changes (for example on a screen or buffer flip), the view jumps along with it so you keep seeing the active image. Turn it off to stay parked at a fixed address.

###### Colors (access tracking)

Every RAM/ROM access briefly lights up in a color, then fades back to the gray **cold** palette. This shows **which areas are being read and written right now, and by whom** (chip, slow, fast RAM and Kickstart ROM):

| Item | set bit (1) | cleared bit (0) |
|---|---|---|
| Cold (idle) |  |  |
| CPU read |  |  |
| CPU write |  |  |
| Blitter write |  |  |

Green = CPU reads, red = CPU writes, blue = blitter writes. Writes win over reads on the same cell. Note: CPU also fetches its instruction code from memory so these areas will also glow green.

###### Fade length

How many emulated frames an access stays highlighted before fading back to the cold palette. The fade freezes while the emulation is paused.

 **250** frames

###### Slomo speed

How fast slow-motion single stepping runs: the delay between the frames it steps through. Lower = faster.

 one step / **500** ms

Many thanks to **Losso / AttentionWhore** for creating the foundation on which this idea and concept were built.

resetting machine, please wait ...

loading please wait ...

converting to Amiga hard disk ...

 workspaces  snapshots

#####  Amiga Operating System ROM

The emulator needs a kickstart system ROM file. Please drag the missing file into the empty chip socket. Or just touch or click the sockets.

##### kickstart rom

...

##### kickstart ext

(optional)

...

Once loaded vAmigaWeb will try to store these files to your browsers local storage. Then on subsequent starts it will take the rom files from your browsers local storage instead of asking you again for them.

AROS [learn more...](https://en.wikipedia.org/wiki/AROS_Research_Operating_System)

[learn more...](https://emutos.sourceforge.io/)

##### vAmigaWebpowered by vAmigaCore []

most settings are permanent and will be saved to your local browser storage

Volume

 show RetroShell icon in menu bar

 show live memory view icon in menu bar

 activity monitor

tap on individual workload charts to visualise bus activity (dma debug)

 dark mode

 pixel art

use shader rendering for full resolution in interlace modes

[software] [gpu shader]

(a change will become effective on next start)

[viewport tracking] [borderless]

[narrow] [standard] [wider] [overscan] [extreme]

(tracking or borderless to auto set Amigas current viewport size)

 NTSC machine and pixel aspect ratio

 cinematic wide screen

 wake lock (request to stay awake while running, prevent thereby system auto off or screen dimming)

[color] [black white] [paper white] [green] [amber] [sepia]

 warp during disk load

 save auto snapshots

 movable action buttons

 'auto selecting' action button groups on media insert

currently auto selecting snapshot names and action button groups based on the filename of the mounted media. (recommended for single disk-based games)

currently auto selecting=off (recommended when all your apps are mainly on a single amiga hard drive.)

[every 2nd vsync] [vsync] [2 frames on vsync] [50%] [75%] [100%] [120%] [160%] [200%]

[0 frame] [1 frame] [2 frames] [3 frames] [4 frames] [5 frames] [6 frames]

run ahead reduces input lag by pre computing frames. The lag improvement is 20ms per number of frames ahead. Basically emulation itself introduces a slight lag of less than 20ms. Therefore, setting run ahead = 1 frame already ensures the original responsive feeling. run ahead = 0 frame saves battery life at the cost of a slight lag.

cut out sprite layers (stencil)

 0

 1

 2

 3

 4

 5

 6

 7

cut out playfield layers (stencil)

 1

 2

compatibility settings

 sprite to sprite collision

 sprite to playfield collision

 playfield to playfield collision

game controller type settings

[1] [2] [3]

one fire button when using virtual touch joystick the right half of screen is that button. All external controller buttons are mapped to button1. (original Amiga games before 1990 had only 1 button)

two fire buttons when using the virtual touch joystick the right half of screen is divided in two vertical stacked touch areas. All external controller buttons are mapped alternating to button1 and button2. When using keyboard joystick emulation button2 is mapped to key 'B'.

three fire buttons when using the virtual touch joystick the right half of screen is divided in three vertical stacked touch areas. All external controller buttons are mapped alternating to button1, 2 and 3. When using keyboard joystick emulation button2 is mapped to key 'B' and button3 to key 'N'.

touch joystick and mouse touchpad layout

 swap move and buttons side

move | buttons the left half of the screen detects movement input and the right half detects button presses

buttons | move the left half of the screen detects button presses and the right half detects movement input

This layout can be more comfortable for left handed players

virtual touch joystick settings

[base moves] [base fixed on first touch] [stationary middle] [stationary bottom]

base moves the base follows your finger when the stick circle passes the boundary of the base circle.

base fixed on first touch joystick base is fixed

stationary middle the base at a fixed middle y position and always visible

stationary bottom the base at a fixed bottom y position and always visible

[0] [4] [8] [12] [14] [16] [20] [24]

touch screen settings for virtual keyboard

[exact timing] [smartphone like] [mix of both]

exact timing autorepeat and simultaneous keycap presses (disables default scroll gestures on keycaps, scroll gesture possible only on gaps around the keys)

smartphone like native scroll gestures on keycaps (press starts after finger is lifted from keycap for a duration of 100ms)

mix of both tries to mix both worlds... i.e. exact timing and simultaneous presses but also scrolls keyboard when swiping the finger on keycaps. disadvantage: also does a keypress when only scrolling was intended

[0.40] [0.45] [0.50] [0.55] [0.60] [0.65] [0.70] [0.75] [0.80] [0.85] [0.90] [0.95] [1.00] [1.10] [1.20] [1.30]

[auto] [0px] [5px] [10px] [15px] [20px] [25px]

[0] [25] [50] [60] [75] [80] [85]

[0] [5] [25] [50] [75] [100]

 haptic key press feedback

 load logging console (after loaded click bottom right button)

[learn more about vAmigaWeb](https://vamigaweb.github.io/doc/about.html)

other members of the vAmiga family:

[take me to vAmiga for Mac](https://dirkwhoffmann.github.io/vAmiga/)

[take me to Coppenheimer](https://coppenheimer.heckmeck.de)

[take me to vAmiga Online](https://www.neoartcr.com/vamiga/)

my 8-Bit brother:

[take me to vc64web](https://vc64web.github.io/doc/about.html)

##### hard reset

By resetting the CPU and the custom chip set, the Amiga will be forced to reboot.

Disk drives will stay connected.

Current program state will be lost.

##### save to local browser space

app title

##### RetroShell

```

```

##### define the action

*create app or game specific keyboard mappings or customized overlay buttons with free positioning that trigger your defined action.*

action button (optional)

specify either a button text or a keyboard shortcut or both

[default] [0.4] [0.6] [0.9] [1.1] [1.3] [1.8] [2.5] [3] [4] [6]

[default] [0.0] [0.1] [0.2] [0.3] [0.4] [0.5] [0.6] [0.7] [0.8] [0.9] [1.0]

keyboard mapping shortcut

specify either a button text or a keyboard shortcut or both

app scope

compose an action sequence, for example

- **loop5{j2fire1=>120ms=>j2fire0=>90ms}** which will shoot 5 times
- or a literal action enclosed in single quotes e.g. **'I am an Amiga.'**
- or key combos e.g. CTRL+W **pressControlLeft=>W=>releaseControlLeft**
- or **pressA=>await_action_button_released=>releaseA**for A keydown on button down and A keyup on button up in locked mode (see settings or below)
- for more complex tasks you can also choose to add a javascript ...

[actionscript] [javascript]

 live complete

 moveable action buttons

#####

vAmigaWeb newer version available

debugger
