//////////////////////////////////////
// Global variables
//////////////////////////////////////
//
// This is coded just for fun ; no, I don't use globals in production code.
// Honest! :-)

// The working image buffer dimensions.
// I use smallish resolution for the HTML5 canvas native resolution,
// so that the code will work even on puny mobile phones.
// (i.e. I don't want the code to require beastly CPUs)
g_width = 320;
g_height = 240;

// The global setInterval timer that calls the 'simulate' function.
g_timer = -1;

// Which tab is currently visible?
g_activeTab = 1;

// Has MathJax been configured in the past?
g_mathJax_configured = false;

// HTML5 canvas variables, shared between the two simulations.
g_dc = null;
g_canvas = null;
g_imageData = null;

// Index of the currently active buffer in our double-buffer scheme
g_1dwave_idx = 0;
g_2dwave_idx = 0;

// The two double-buffers of data - 1d and 2d
g_1dwave_y = [ new Float32Array(g_width), new Float32Array(g_width)];
g_2dwave_y = [ new Float32Array(g_width*g_height), new Float32Array(g_width*g_height)];

// Lookup table for the 2d simulation.
g_2d_offsets = new Int32Array(g_height);
for(var ii=0; ii<g_height; ii++) {
    g_2d_offsets[ii] = g_width*ii;
}

// The backlog of pixel(s) to clear when we pull the string
g_pullBacklog = [];

// Function that checks whether we have a working HTML5 canvas
// and then sets up the canvas related globals and the timer.
function setupCanvasAndStartSimulation() {
    var is1Dsim = g_activeTab === 0;
    g_canvas = document.getElementById(is1Dsim?"1dwaveDC":"2dwaveDC");
    if (!g_canvas.getContext) {
        alert("You are using an old browser - please use a recent Firefox / Chrome / Opera / Safari");
        return false;
    }
    g_dc = g_canvas.getContext("2d");
    if (!is1Dsim) {
        g_canvas.removeEventListener('mousedown', rainDrop);
        g_canvas.addEventListener('mousedown', rainDrop);
    }
    // ...and start the simulation!
    if (g_timer === -1) {
        g_timer = setInterval(function() { simulate(); }, 20);
    }
    return true;
}

////////////////////////////////////////////////////////////////////
// 1D wave simulation
////////////////////////////////////////////////////////////////////

// Quickly plot two green or black pixels in the 1D canvas image data
function qplot(x, y, color) {
    if (y<0 || x<0 || y>=g_height-1 || x>=g_width)
        return;
    var ofs = Math.floor(y)*g_width*4 + Math.floor(x)*4;
    g_imageData[ofs + 0] = 0;
    g_imageData[ofs + 1] = color;
    g_imageData[ofs + 2] = 0;
    g_imageData[ofs + 3] = 255;
    g_imageData[ofs + 4*g_width + 0] = 0;
    g_imageData[ofs + 4*g_width + 1] = color;
    g_imageData[ofs + 4*g_width + 2] = 0;
    g_imageData[ofs + 4*g_width + 3] = 255;
}

// Pull the string at the middle
function pull() {
    // If there's no simulation running, set it up.
    if (g_timer === -1) {
        if (!setupCanvasAndStartSimulation())
            return;
    }
    // Now, pull the middle string sample to minimum height.
    // Also, mark its old value in the backlog, so we'll clear
    // that old pixel in the main loop.
    var yOldest = g_1dwave_y[(g_1dwave_idx+1) % 2];
    g_pullBacklog.push(yOldest[Math.floor(g_width/2)]);
    // And now, pull!
    yOldest[Math.floor(g_width/2)] = g_height/2;
}

// The theory behind the 1d wave calculation is the following:
// Assume we have a wave function, f(x), (x=horizontal pixel) as it is at time (n).
// We want to find how the values will change at time (n+1).
//
// Consider the individual pixels to represent the water molecules.
// Assume that each molecule is influenced only by its two neighbours,
// as if they are connected to it with "springs":
//
//      xxx                   xxx
//     x    x                R
//    x      x              O._
//            x            L |\
//  ---------------------------\------
//              x        x      \
//               x      x        `---- This point (O) is only influenced
//                x    x               by the forces of two "springs":
//                 xxxx                the one attached to its left
//                                     neighbour(L) and the one attached
//                                     to its right neighbour(R)
// Using Euler integration of Neutonian laws, we will have for the point O:
// (p=position, v=velocity, a=acceleration)
//
//
// p    = p  + v        (new position = old position + velocity)
//  n+1    n    n
//
//
// v  = v    + a        (velocity = old velocity + old acceleration)
//  n    n-1    n-1
//
//                      (springs cause acceleration linear to distance)
//
// a    = k * (pL    - p    ) + k * (pR    - p    )  (k is the spring coeff)
//  n-1          n-2    n-2            n-2    n-2
//
//
// This would work, but would require quite a lot of calculations...
// Instead, we will use the acceleration at time n+2 (instead of n-1),
// which basically means that we will delay the effects of the springs
// for three time slots - as if the springs have a "delayed" effect.
//
// We will also set k=1. Look at what happens (we replace v  first):
//                                                         n
//
//
// p    = p  + v    + a    = (aprox) p  + (p  - p   )  + a
//  n+1    n    n-1    n-1            n     n    n-1      n+2
//
//      = 2*p  - p    + pL    - p   + pR    - p
//           n    n-1     n      n      n      n
//
//      = pL  + pR  - p
//          n     n    n-1
//
// So the end result is amazingly simple: we add the values of the two
// neighbouring pixels, and subtract the old value we used to have!
// 
// Since the springs are losing power with each iteration, we will also
// scale the output of the last equation so that it diminishes over time
// (e.g.  multiply by a factor of 0.995):

function simulate1d() {
    var image = g_dc.getImageData(0, 0, g_width, g_height);
    g_imageData = image.data;
    // Double buffering two string 'instances'
    var yOldest = g_1dwave_y[g_1dwave_idx];
    g_1dwave_idx = (g_1dwave_idx+1) % 2;
    var yOld=g_1dwave_y[g_1dwave_idx], i=0;

    // Erasing the pixels of the 'pull' backlog
    for(; i<g_pullBacklog.length; i++) {
        qplot(g_width/2, g_height/2 + g_pullBacklog[i], 0);
    }
    g_pullBacklog = [];

    for(i=1;i<g_width-1; i++) {
        // Erasing the old string instance pixels
        qplot(i, g_height/2 + yOld[i], 0);
        // Computing our awesome equation
        var val = yOld[i-1] + yOld[i+1] - yOldest[i];
        yOldest[i] = 0.995*val;
        // Plotting the new string instance pixels
        qplot(i, g_height/2 + yOldest[i], 255);
    }
    // Display the freshly computed HTML5 canvas image
    g_dc.putImageData(image, 0, 0);
}

////////////////////////////////////////////////////////////////////
// 2D wave simulation
////////////////////////////////////////////////////////////////////

// When the user clicks anywhere in our blue pool...
function rainDrop(evt) {
    // ...first figure out where he clicked, in terms of our canvas' native coordinates:
    evt = evt || window.event;
    var x = g_width*(evt.pageX - g_canvas.offsetLeft - $('#tabs')[0].offsetLeft)/g_canvas.clientWidth;
    var y = g_height*(evt.pageY - g_canvas.offsetTop - $('#tabs')[0].offsetTop)/g_canvas.clientHeight;

    // And then, pull that water molecule to maximum height...
    var yOldest = g_2dwave_y[(g_2dwave_idx+1) % 2];
    yOldest[g_2d_offsets[Math.floor(y)]+Math.floor(x)] = 8.0;

    // In fact, the maximum height is 1.0 - but by pulling it to 8,
    // we will in fact be displaying this wave as 8 closely
    // diminishing ones (see the scaling by 127 below and what
    // it means for values larger than 255...)
}

// (Continuing from the comments of 'simulate1d' above...)
//
// ...for the corresponding two-dimensional problem,
// we just average the effects of the X- and Y- coordinate waves:
//
// p   (i,j) = 0.5 (p                  (i,j) + p                (i,j)
//  n+1              n+1,HorizontalWave         n+1,VerticalWave
//  
//           = 0.5 (0.999(p (i-1,j) + p (i+1,j) - p   (i,j)) + 
//                         n           n           n-1
//
//                + 0.999(p (i,j-1) + p (i,j+1) - p   (i,j)))
//                         n           n           n-1
//
// p   (i,j) = 0.999(0.5(p (i-1,j) + p (i+1,j) + p (i,j-1) + p (i,j+1))  - p   (i,j) ) 
//  n+1                   n           n           n           n             n-1
//
// Which translates to: we add the 4 neighbouring pixels, divide by 2,
// subtract the previous frame value, and scale by our energy loss coefficient.
//
// Simple! :-)

function simulate2d() {
    var image = g_dc.getImageData(0, 0, g_width, g_height);
    // Double buffering of the two pool 'instances'
    var yOldest = g_2dwave_y[g_2dwave_idx];
    g_2dwave_idx = (g_2dwave_idx+1) % 2;
    var yOld=g_2dwave_y[g_2dwave_idx];
    // Now apply the formula...
    for(var i=1; i<g_height-1; i++) {
        // ...and pre-compute the line offsets, for speed.
        // (probably unnecessary in the case of V8,
        //  but I did do this in the libSDL code, so I ported it over)
        var     lineOffset = g_2d_offsets[i];
        var prevLineOffset = g_2d_offsets[i-1];
        var nextLineOffset = g_2d_offsets[i+1];
        for(var j=1; j<g_width-1; j++) {
            var val = (
                yOld[prevLineOffset + j-1] + yOld[prevLineOffset + j+1] + 
                yOld[nextLineOffset + j-1] + yOld[nextLineOffset + j+1])/2 - yOldest[lineOffset + j];
            yOldest[lineOffset + j] = (0.99999*val);
            // Scale between 0 and 255...
            var color = (127.0+127.0*0.99999*val);
            // R G [B] [A] - water is blue, no?
            image.data[4*(lineOffset+j) + 0] = 0;
            image.data[4*(lineOffset+j) + 1] = 0;
            image.data[4*(lineOffset+j) + 2] = color;
            image.data[4*(lineOffset+j) + 3] = 255;
        }
    }
    g_dc.putImageData(image, 0, 0);
}

// The function called by setInterval every 20ms (maximum refresh rate: 50Hz).
function simulate() {
    // Depending on the active TAB, call the proper simulator.
    if (g_activeTab === 0) {
        simulate1d();
    } else if (g_activeTab === 1) {
        simulate2d();
    } else {
        // In the rest of the TABs (the 'Theory' and 'Javascript' sections)
        // disable the simulation (don't waste tablet/phone batteries!)
        if (g_timer !== -1) {
            clearInterval(g_timer);
            g_timer = -1;
        }
    }
}

// Called from some HTML side links to switch the active jQueryUI tab.
function switchToTab(tab) {
    jQuery('#tabs').tabs("option", "active", tab);
    return false;
}

// The main entrypoint:
jQuery(document).ready(function() {
    // Create a jQueryUI tab, and show the first tab ('1D wave'):
    jQuery( "#tabs" ).tabs({
        activate: function(event, ui) {
            g_activeTab = {
                '1-dimension wave (string)': 0,
                '2-dimension waves (water)': 1,
                'The theory':                2,
                'The code':                  3
            }[ui.newTab[0].children[0].text];
            if (g_activeTab === 0 || g_activeTab === 1)
                setupCanvasAndStartSimulation();
            else if (g_activeTab === 2) {
                if (g_mathJax_configured === false) {
                    g_mathJax_configured = true;
                    MathJax.Hub.Configured();
                }
            }
        },
        active: 1
    });
    setupCanvasAndStartSimulation();
});
