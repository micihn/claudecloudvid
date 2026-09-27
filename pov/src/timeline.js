// Every time in the film, measured from the first 30 s of "Point of View" (onsets, band energy, cuts).
// The picture reads only from here, so a re-cut to other music means editing this file.
export const FPS = 30, DUR = 30;

export const T = {
  cut1: 6.97,                                        // the opening swell stops dead
  clicks: [7.129, 7.326, 7.506, 7.680, 7.860],       // five small clicks in the silence -> "Look."
  hit0: 8.046,                                       // first hit + stepped glitch tone (8.05-8.70)
  step: 8.21,                                        // the tone's pitch step
  shots: [8.046, 8.789, 9.799, 10.455, 11.494, 11.935],  // hard hits -> jump cuts to new points of view
  blip: [11.28, 11.66],                              // a short glitch tone -> scan line
  burst1: 12.841,                                    // noise burst into the drone
  orbit: 12.87,                                      // sub drone starts: one continuous camera move
  align: 22.9,                                       // the second swell peaks: the tangle is a flower
  flatten: 23.1,                                     // the tangle's depth collapses into the drawing
  paint: 23.95,                                      // watercolour floods the petals, they cup and bloom
  climax: 25.9,
  cut2: 26.715,                                      // the build stops
  burst2: 27.0,                                      // broken glitch burst -> the wordmark
  burst2End: 27.34,
  thump: 28.323,                                     // low thump -> "A digital atelier"
  glitch2: 28.723,
  silence: 29.124,                                   // total silence: everything holds
};

// small ticks and glitches between the big events: (time, strength)
export const TICKS = [
  [8.429, 0.35], [9.445, 0.25], [9.613, 0.35], [9.967, 0.3], [10.159, 0.25], [11.651, 0.45],
  [13.572, 0.25], [13.746, 0.3], [27.214, 0.5], [27.324, 0.7], [27.545, 0.6], [28.607, 0.3],
  [28.857, 0.35], [29.037, 0.3],
];
