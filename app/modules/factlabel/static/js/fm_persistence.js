// import { get_property } from './fm_fact_label.js';

/**
 * Set-up the save PNG button.
 */
d3.select('#savePNG').on('click', function () {
    var chart = d3.select(".chart");
    chart.selectAll("#collapseIcon").attr("visibility", "hidden");
    var blob = rasterize(chart.node());
    blob.then(value => {
        saveAs(value, get_property(fmData, 'Name').value + ".png");
    });
    //chart.selectAll("#collapseIcon").attr("visibility", "visible");
    newData = filterData(ALL_DATA);
    redrawLabel(newData);
});

/**
 * Set-up the save SVG button.
 */
d3.select('#saveSVG').on('click', function () {
    var chart = d3.select(".chart");
    chart.selectAll("#collapseIcon").attr("visibility", "hidden");
    var blob = serialize(chart.node());
    saveAs(blob, get_property(fmData, 'Name').value + ".svg");
    //chart.selectAll("#collapseIcon").attr("visibility", "visible");
    newData = filterData(ALL_DATA);
    redrawLabel(newData);
});

/**
 * Set-up the save TXT button.
 */
d3.select('#saveTXT').on('click', function () {
    var blob = new Blob([fmCharacterizationStr], { type: "text/plain" });
    saveAs(blob, get_property(fmData, 'Name').value + ".txt");
});

/**
 * Set-up the save JSON button.
 */
d3.select('#saveJSON').on('click', function () {
    //var strJson = JSON.stringify(fmCharacterizationStringJson, null, 4);
    var blob = new Blob([fmCharacterizationJSONStr], { type: "application/json" });
    saveAs(blob, get_property(fmData, 'Name').value + ".json");
});

/**
 * Generic code to download a file available in the server.
 * (Not used actually.)
 */
function downloadUsingAnchorElement() {
    const anchor = document.createElement("a");
    anchor.href = IMG_URL;
    anchor.download = FILE_NAME;
    
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
}

/**
 * Third-party code:
 * - For saving SVG and PNG: https://observablehq.com/@mbostock/saving-svg
 * - FileSaver (for saving files on the clien-side): https://github.com/eligrey/FileSaver.js/
 */

const xmlns = "http://www.w3.org/2000/xmlns/";
const xlinkns = "http://www.w3.org/1999/xlink";
const svgns = "http://www.w3.org/2000/svg";

function serialize(svg) {
    svg = svg.cloneNode(true);
    const fragment = window.location.href + "#";
    const walker = document.createTreeWalker(svg, NodeFilter.SHOW_ELEMENT);
    while (walker.nextNode()) {
        for (const attr of walker.currentNode.attributes) {
            if (attr.value.includes(fragment)) {
                attr.value = attr.value.replace(fragment, "#");
            }
        }
    }
    svg.setAttributeNS(xmlns, "xmlns", svgns);
    svg.setAttributeNS(xmlns, "xmlns:xlink", xlinkns);
    const serializer = new window.XMLSerializer;
    const string = serializer.serializeToString(svg);
    return new Blob([string], { type: "image/svg+xml" });
}

function rasterize(svg) {
    let resolve, reject;
    const promise = new Promise((y, n) => (resolve = y, reject = n));
    const image = new Image;
    image.onerror = reject;
    image.onload = () => {
        const rect = svg.getBoundingClientRect();
        const context = context2d(rect.width, rect.height);
        context.drawImage(image, 0, 0, rect.width, rect.height);
        context.canvas.toBlob(resolve);
    };
    image.src = URL.createObjectURL(serialize(svg));
    return promise;
}

function context2d(width, height, dpi) {
    if (dpi == null) dpi = devicePixelRatio;
    var canvas = document.createElement("canvas");
    canvas.width = width * dpi;
    canvas.height = height * dpi;
    canvas.style.width = width + "px";
    var context = canvas.getContext("2d");
    context.scale(dpi, dpi);
    return context;
}
