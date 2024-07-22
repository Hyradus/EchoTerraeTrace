---
name: Bug report
about: Create a report to help us improve
title: ''
labels: ''
assignees: ''

---

Bug #1

**Describe the bug**
Changing "RGRM Amplitude Index" slider value doesn't affect acquisition window.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to the left top of the tool, where you can find the "RGRM Amplitude Index" slider 
2. Click on the "little circle" and change its position along the slider bar.
3. See error

**Expected behavior**
I would expect changes in the acquisition window, based on different frequencies etc.

**Desktop (please complete the following information):**
 - OS: Windows Subsystem for Linux (WSL 2) (specifically Ubuntu 22.04.2 LTS)
 - Browser : Google Chrome
 - Version : 126.0.6478.183


Bug #2

**Describe the bug**
"X-Axis inversion" of the graph showing the comparison between "side power profiles" of Frequency 1 and Coherent Simulation.
The x-axis could show an unexpected positive range from 0 to 60, which doesn't make sense, because the measured quantity is the power attenuation (in terms of dB) of an electromagnetic signal. 
No or very little power profiles can be seen, considering that we obviously don't expect gains of power from surface reflections, physically talking.

**To Reproduce**
Steps to reproduce the behavior:
1. Load the desired track from the list
2. See error to the right of the acquisition window.

**Expected behavior**
The expected behaviour from the above-mentioned graph would be to have a negative x-axis (with a range from - 60 dB to 0 dB),
in order to correctly view "side" power attenuation curves.

**Desktop (please complete the following information):**
 - OS: Windows Subsystem for Linux (WSL 2) (specifically Ubuntu 22.04.2 LTS)
 - Browser : Google Chrome
 - Version : 126.0.6478.183

Bug #3

**Describe the bug**
Immobilized crosshair in elevation profiles by MOLA topography.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to "Elevation Profiles" window (bottom of the tool page).
2. Move the cursor wherever you want in the window.
3. See error: the crosshair doesn't follow the cursor movements.

**Expected behavior**
Trivially, we would expect that the crosshair would be able to follow the cursor movements.

**Desktop (please complete the following information):**
 - OS: Windows Subsystem for Linux (WSL 2) (specifically Ubuntu 22.04.2 LTS)
 - Browser : Google Chrome
 - Version : 126.0.6478.183
