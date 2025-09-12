   
const POINT_TO_PIXEL = 1.3281472327365;
//const TITLE_FONT_FAMILY = "Franklin Gothic Heavy";
const TITLE_FONT_FAMILY = "'Libre Franklin', sans-serif";
const TITLE_FONT_SIZE = "24pt";
const DESCRIPTION_FONT_FAMILY = "Helvetica";
const DESCRIPTION_FONT_SIZE = "8pt";
const PROPERTY_FONT_FAMILY = "Helvetica";
const PROPERTY_FONT_SIZE = "12pt";
const VALUES_FONT_FAMILY = "Helvetica";
const VALUES_FONT_SIZE = "10pt";
const COLLAPSEICON_FONT_SIZE = "8pt";
const PROPERTY_INDENTATION = 2;
const TOP_MARGING = 20;
const LEFT_MARGING = 5;
const MAIN_RULE_HEIGHT = 7 * POINT_TO_PIXEL;
const SECONDARY_RULE_HEIGHT = .25 * POINT_TO_PIXEL;
const MARGING_BETWEEN_PROPERTIES = 3;
const PROPERTIES_VALUES_SPACE = 10;
const PROPERTIES_RATIO_SPACE = 3;

const EXPANDED_ICON = '\uf150';
const COLLAPSED_ICON = '\uf152';
const HREF_ICON = '\uf0ac';

// GLOBAL VARIABLES
var maxWidth;
var currentHeight;
var maxIndentationWidth;
var maxNameWidth
var maxValueWidth;
var maxRatioWidth;
var PROPERTY_HEIGHT;
var x;
var yRule1;
var yMetrics;
var tooltip;
var contentDetail;
var VISIBLE_PROPERTIES = {};
var ALL_DATA;
var chart;

var IMPORTS = ['https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@900',
   'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.1.1/css/all.min.css'];


function drawFMFactLabel(data) {
   console.log("Inside drawFMFactLabel");
   console.log(data);
   chart = d3.select(".chart");  // The svg 

   // chart.append('defs')
   //    .append('style')
   //    .attr('type', 'text/css')
   //    .text("@import url('https://fonts.googleapis.com/css2?family=Libre+Franklin:wght@900');");
   chart.selectAll('defs')
      .data(IMPORTS, d => d)
      .join("style")
      .attr('type', 'text/css')
      .text(function (d) { return "@import url('" + d + "');"; });

   // Create a div for mouse hover effect
   tooltip = d3.select("body").append("div").attr("class", "tooltip").style("opacity", 0)
      .style("position", "absolute")
      .style("text-align", "left")
      .style("padding", "0.1rem")
      .style("background", "#FFFFFF")
      .style("color", "#313639")
      .style("border", "1px solid #313639")
      .style("border-radius", "8px")
      .style("pointer-events", "none")
      .style("font-size", "0.8rem")
   
   // Create a div to show the content detail on mouse click
   contentDetail = d3.select("body").append("div").attr("class", "contentDetail").style("opacity", 0)
   .style("position", "absolute")
   .style("text-align", "left")
   .style("padding", "0.1rem")
   .style("background", "#FFFFFF")
   .style("color", "#313639")
   .style("border", "1px solid #313639")
   .style("border-radius", "8px")
   .style("font-size", "0.8rem")
   //.style("width", "400px")
   .on('mouseout', function (event, d) {
      d3.select(this).transition()
         .duration('50')
         .style('opacity', 0);
   });

   ALL_DATA = data
   // Initialize visible properties   
   for (let p of data.metadata) { VISIBLE_PROPERTIES[p.name] = true; }
   for (let p of data.metrics) { VISIBLE_PROPERTIES[p.name] = true; }
   for (let p of data.analysis) { VISIBLE_PROPERTIES[p.name] = true; }

   // Calculate maximum width for the label.
   //var maxWidth = Math.max(calculateTotalMaxWidth(data.metrics), calculateTotalMaxWidth(data.analysis));
PROPERTY_HEIGHT = textSize("Any text", PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE, "bold").height;

maxIndentationWidth = Math.max(
    calculateMaxIndentationWidth(data.metrics),
    calculateMaxIndentationWidth(data.analysis)
);
maxNameWidth = Math.max(
    calculateMaxNameWidth(data.metrics),
    calculateMaxNameWidth(data.analysis)
);
maxValueWidth = Math.max(
    calculateMaxValueWidth(data.metrics),
    calculateMaxValueWidth(data.analysis)
);
maxRatioWidth = Math.max(
    calculateMaxRatioWidth(data.metrics),
    calculateMaxRatioWidth(data.analysis)
);

maxWidth =
    maxIndentationWidth +
    maxNameWidth +
    PROPERTIES_VALUES_SPACE +
    maxValueWidth +
    PROPERTIES_RATIO_SPACE +
    maxRatioWidth +
    LEFT_MARGING;

// en vez de width fijo, usamos viewBox y width="100%"
const bboxHeight = 800; // valor temporal, luego lo ajustas con getBBox()
chart
    .attr("viewBox", `0 0 ${maxWidth} ${bboxHeight}`)
    .attr("preserveAspectRatio", "xMinYMin meet")
    .attr("width", "100%")
    .attr("height", bboxHeight);


   x = d3.scaleLinear().domain([0, maxWidth]).range([0, maxWidth]);

   // Title
   var titleSize = textSize(get_property(data, "Name").result, TITLE_FONT_FAMILY, TITLE_FONT_SIZE);
   var yTitle = TOP_MARGING;
   var title = chart.append("g").attr("transform", "translate(0," + yTitle + ")");
   title.append("text")
      .text(get_property(data, 'Name').result)
      .attr("x", function (d) { return x(maxWidth / 2); })
      //.attr("y", 3)
      .attr("text-anchor", "middle")
      .attr("dominant-baseline", "central")
      .attr("font-family", TITLE_FONT_FAMILY)
      .attr("font-size", TITLE_FONT_SIZE)
      .attr("font-weight", "bold");

   // Description
   var yDescription = yTitle + titleSize.height + 1;
   var indentationDescription = textSize("-".repeat(PROPERTY_INDENTATION), DESCRIPTION_FONT_FAMILY, DESCRIPTION_FONT_SIZE).width;
   var description = chart.append("g").attr("transform", "translate(0," + yDescription + ")");
   description.append("text")
      .text(get_property(data, 'Description').result)
      .attr("x", function (d) { return x(indentationDescription) })
      //.attr("y", BAR_HEIGHT / 2)
      .attr("font-family", DESCRIPTION_FONT_FAMILY)
      .attr("font-size", DESCRIPTION_FONT_SIZE)
      .call(wrap, maxWidth - indentationDescription);
   var descriptionSize = description.node().getBBox();

   // Keywords
   var keywordHeight = yDescription + descriptionSize.height + 1;
   if (get_property(data, 'Tags').result === null) {
      var keywordsSize = descriptionSize;
   } else {
      var keywords = chart.append("g").attr("transform", "translate(0," + keywordHeight + ")");
      addMetadata(keywords, "Tags:", get_property(data, 'Tags').result);
      var keywordsSize = keywords.node().getBBox();
   }

   // Author
   var authorHeight = keywordHeight + keywordsSize.height;
   if (get_property(data, 'Author').result === null) {
      var authorSize = { "width": 0, "height": 0 };
   } else {
      var author = chart.append("g").attr("transform", "translate(0," + authorHeight + ")");
      addMetadata(author, "Author:", get_property(data, 'Author').result);
      var authorSize = author.node().getBBox();
   }

   // Year
   var yearHeight = authorHeight + authorSize.height;
   if (get_property(data, 'Year').result === null) {
      var yearSize = { "width": 0, "height": 0 };
   } else {
      var year = chart.append("g").attr("transform", "translate(0," + yearHeight + ")");
      addMetadata(year, "Year:", get_property(data, 'Year').result);
      var yearSize = year.node().getBBox();
   }

   // Domain
   var domainHeight = yearHeight + yearSize.height;
   if (get_property(data, 'Domain').result === null) {
      var domainSize = { "width": 0, "height": 0 };
   } else {
      var domain = chart.append("g").attr("transform", "translate(0," + domainHeight + ")");
      addMetadata(domain, "Domain:", get_property(data, 'Domain').result);
      var domainSize = domain.node().getBBox();
   }

   // Reference
   if (!get_property(data, 'Reference').result == "") {
      var reference = chart.append("g").attr("transform", "translate(0," + (domainHeight + domainSize.height - MAIN_RULE_HEIGHT - 10) + ")");
      reference.append('a')
         .attr("id", "hrefIcon")
         .attr("href", get_property(data, 'Reference').result)
         .append("text")
         .attr("text-anchor", "end")
         .attr("x", maxWidth - 5)
         .attr("dy", ".35em")
         .attr("y", PROPERTY_HEIGHT / 2)
         .attr('font-family', 'FontAwesome')
         .attr('font-size', "12pt")
         .text(HREF_ICON)
         .attr("cursor", "pointer");
   }

   // Middle rule 1
   yRule1 = domainHeight + domainSize.height;
   chart.append("g").attr("id", "rule1");
   drawRule("rule1", yRule1);

   // Metrics
   yMetrics = yRule1 + MAIN_RULE_HEIGHT;
   chart.append("g").attr("id", "metrics").attr("transform", "translate(0," + yMetrics + ")");
   updateProperties(data.metrics, "metrics");

   // Middle rule 2
   var yRule2 = yMetrics + PROPERTY_HEIGHT * data.metrics.length;
   chart.append("g").attr("id", "rule2");
   drawRule("rule2", yRule2);

   // Analysis
   var yAnalysis = yRule2 + MAIN_RULE_HEIGHT;
   chart.append("g").attr("id", "analysis").attr("transform", "translate(0," + yAnalysis + ")");
   updateProperties(data.analysis, "analysis");

   // Border of the label
   var maxHeight = yAnalysis + MARGING_BETWEEN_PROPERTIES + PROPERTY_HEIGHT * data.analysis.length;
   chart.append("rect").attr("id", "border");
   drawBorders(maxWidth, maxHeight);
const bbox = chart.node().getBBox();
chart
    .attr("viewBox", `0 0 ${maxWidth} ${bbox.height + 10}`)
    .attr("height", bbox.height + 10);

   collapseSubProperties(data);
}

function addMetadata(element, key, value) {
   element.append("text")
      .text(key)
      .attr("x", function (d) { return x(PROPERTY_INDENTATION * 3) })
      .attr("font-family", DESCRIPTION_FONT_FAMILY)
      .attr("font-size", DESCRIPTION_FONT_SIZE)
      .attr("font-weight", "bold");
   element.append("text")
      .text(value)
      .attr("x", function (d) { return x(6 * PROPERTY_INDENTATION + textSize(key, DESCRIPTION_FONT_FAMILY, DESCRIPTION_FONT_SIZE).width); })
      .attr("font-family", DESCRIPTION_FONT_FAMILY)
      .attr("font-size", DESCRIPTION_FONT_SIZE)
      .call(wrap, maxWidth - (6 * PROPERTY_INDENTATION + textSize(key, DESCRIPTION_FONT_FAMILY, DESCRIPTION_FONT_SIZE).width));
}

function updateProperties(data, id) {
   d3.select("#" + id)
      .selectAll("g")
      .data(data, d => d)
      .join(
         function (enter) {
            // Indentation
            var property = enter.append("g").attr("id", function (d) { return d.name; }).attr("transform", function (d, i) { return "translate(0," + i * PROPERTY_HEIGHT + ")"; });
            property.append("rect")
               .attr("id", "indentation")
               .attr("x", function (d) { return x(0); })
               .attr("y", PROPERTY_HEIGHT)
               .attr("dy", ".35em")
               .attr("width", function (d) { return get_indentation(d); })
               .attr("height", PROPERTY_HEIGHT)
               .attr("fill", "white");

            var collapseIcon = property.append('text')
               .attr("id", "collapseIcon")
               .attr("x", function (d) { return get_indentation(d); })
               .attr("dy", ".35em")
               .attr("y", PROPERTY_HEIGHT / 2)
               .attr('font-family', 'FontAwesome')
               .attr('font-size', COLLAPSEICON_FONT_SIZE)
               .text(function (d) { return hasChildrenProperties(d) && getChildrenProperties(data, d, false).length == 0 ? COLLAPSED_ICON : EXPANDED_ICON; })
               .attr("visibility", function (d) { return hasChildrenProperties(d) ? "visible" : "hidden"; })
               .attr("cursor", "pointer")
               .on("click", function (p, d) { hasChildrenProperties(d) && getChildrenProperties(data, d, false).length == 0 ? expandProperty(ALL_DATA, d) : collapseProperty(ALL_DATA, d); });

            var collapseIconWidth = collapseIcon.node() === null ? 0 : collapseIcon.node().getBBox().width;

            // Property name
            property.append("text")
               .attr("id", "propertyName")
               .attr("text-anchor", "start")
               .attr("x", function (d) { return get_indentation(d) + collapseIconWidth + PROPERTY_INDENTATION; })
               .attr("y", PROPERTY_HEIGHT / 2)
               .attr("dy", ".35em")
               .attr("font-family", PROPERTY_FONT_FAMILY)
               .attr("font-size", PROPERTY_FONT_SIZE)
               .attr("font-weight", function (d) { return parseInt(d.level, 10) == 0 ? "bold" : "normal"; })
               .text(function (d) { return d.name; })
               .on('mouseover', function (event, d) {
                  const [posX, posY] = d3.pointer(event, chart.node());
                  d3.select(this).transition()
                     .duration('50')
                     .attr('opacity', 0.85);
                  //Makes the new div appear on hover:
                  tooltip.transition()
                     .duration(50)
                     .style("opacity", 1);
                  tooltip.html(d.documentation)
                     .style("left", (event.pageX + 10) + "px")
                     .style("top", (event.pageY - 15) + "px");
               })
               .on('mouseout', function (event, d) {
                  d3.select(this).transition()
                     .duration('50')
                     .attr('opacity', 1);
                  //Makes the new div disappear:
                  tooltip.transition()
                     .duration('50')
                     .style("opacity", 0);
               })
               .on("click", function (event, d) { 
                  tooltip.transition()
                     .duration('50')
                     .style("opacity", 0);
                  contentDetail.transition()
                     .duration(50)
                     .style("opacity", 1);
                  contentDetail.html(d.result)
                     .style("left", (event.pageX + 10) + "px")
                     .style("top", (event.pageY - 15) + "px")
               });

            // Property value (size)
            property.append("text")
               .attr("id", "value")
               .attr("text-anchor", "end")
               .attr("x", function (d) { return x(maxIndentationWidth + maxNameWidth + PROPERTIES_VALUES_SPACE + maxValueWidth); })
               .attr("y", PROPERTY_HEIGHT / 2)
               .attr("dy", ".35em")
               .attr("font-family", PROPERTY_FONT_FAMILY)
               .attr("font-size", VALUES_FONT_SIZE)
               .attr("font-weight", "bold")
               .text(function (d) { return get_value(d); });

            // Property ratio
            property.append("text")
               .attr("id", "ratio")
               .attr("text-anchor", "end")
               .attr("x", function (d) { return x(maxWidth - LEFT_MARGING); })
               .attr("y", PROPERTY_HEIGHT / 2)
               .attr("dy", ".35em")
               .attr("font-family", PROPERTY_FONT_FAMILY)
               .attr("font-size", VALUES_FONT_SIZE)
               .attr("font-weight", "bold")
               .text(function (d) { return get_ratio(d); });
            return property;
         },
         function (update) {
            update.select("#collapseIcon")
               .text(function (d) { return hasChildrenProperties(d) && getChildrenProperties(data, d).length == 0 ? COLLAPSED_ICON : EXPANDED_ICON; })
               .attr("visibility", function (d) { return hasChildrenProperties(d) ? "visible" : "hidden"; })
               .on("click", function (p, d) { hasChildrenProperties(d) && getChildrenProperties(data, d).length == 0 ? expandProperty(ALL_DATA, d) : collapseProperty(ALL_DATA, d); });
            return update;
         },
         function (exit) {
            return exit.remove();
         }
      );
   drawSecondaryRules(data)
}

function drawRule(id, yPosition) {
   d3.select("#" + id)
      .attr("transform", "translate(0," + yPosition + ")")
      .append("rect")
      .attr("height", MAIN_RULE_HEIGHT)
      .attr("width", maxWidth);
}

function drawBorders(width, height) {
   d3.select("#border")
      .attr("x", 0)
      .attr("y", 0)
      .attr("width", width)
      .attr("height", height)
      .style("stroke", "black")
      .style("fill", "none")
      .style("stroke-width", "3pt");
}

/**
 * 
 * @param {any} d A FM property.
 * @returns The value for the property.
 */
function get_value(d) {
   return d.size === null ? d.result : d.size;
}

/**
 * 
 * @param {any} d A FM property.
 * @returns The percentage for the property.
 */
function get_ratio(d) {
   return d.ratio === null ? "" : "(" + Math.round((d.ratio + Number.EPSILON) * 100) + "%)";
}

/**
 * 
 * @param {any} d A FM property. 
 * @returns The indentation width.
 */
function get_indentation(d) {
   return textSize("-".repeat(1 + PROPERTY_INDENTATION * parseInt(d.level, 10)), PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE).width;
}

/**
 * 
 * @param {Array} data Dataset.
 * @param {String} propertyName Property's name.
 * @returns The property by its name. 
 */
function get_property(data, propertyName) {
   for (let p of data.metadata) {
      if (p.name == propertyName) {
         return p;
      }
   }
   for (let p of data.metrics) {
      if (p.name == propertyName) {
         return p;
      }
   }
   for (let p of data.analysis) {
      if (p.name == propertyName) {
         return p;
      }
   }
}

function get_property_in_data(data, propertyName) {
   for (let p of data) {
      if (p.name == propertyName) {
         return p;
      }
   }
   return null;
}

/**
 * Wrap the text D3 Object to the given width.
 * 
 * @param {Object} text Text to be wrapped.
 * @param {String} width Width used for wrapping.
 */
function wrap(text, width) {
   text.each(function () {
      var text = d3.select(this),
         words = text.text().split(/\s+/).reverse(),
         word,
         line = [],
         lineNumber = 0, //<-- 0!
         lineHeight = 1.2, // ems
         x = text.attr("x"), //<-- include the x!
         y = text.attr("y"),
         dy = text.attr("dy") ? text.attr("dy") : 0; //<-- null check
      tspan = text.text(null).append("tspan").attr("x", x).attr("y", y).attr("dy", dy + "em");
      while (word = words.pop()) {
         line.push(word);
         tspan.text(line.join(" "));
         if (tspan.node().getComputedTextLength() > width) {
            line.pop();
            tspan.text(line.join(" "));
            line = [word];
            tspan = text.append("tspan").attr("x", x).attr("y", y).attr("dy", ++lineNumber * lineHeight + dy + "em").text(word);
         }
      }
   });
}

/**
 * Measure text size in pixels with D3.js
 * 
 * Usage: textSize("This is a very long text"); 
 * => Return: Object {width: 140, height: 15.453125}
 * 
 * @param {String} text 
 * @param {String} fontFamily 
 * @param {String} fontSize 
 * @param {String} fontWeight
 * @returns Object including width and height.
 */
function textSize(text, fontFamily, fontSize, fontWeight = "normal") {
   var container = d3.select('body').append('svg');
   container.append('text').text(text).attr("font-family", fontFamily).attr("font-size", fontSize).attr("font-weight", fontWeight);
   var size = container.node().getBBox();
   container.remove();
   return { width: size.width, height: size.height };
}

/**
 * 
 * @param {Array} data    Array of properties.
 * @param {any} property  Property.
 * @returns List of children of the property.
 */
function getChildrenProperties(data, property, recursively) {
   var children = [];
   for (let p of data) {
      if (p.parent == property.name) {
         children.push(p);
      }
   }
   if (recursively) {
      for (let c of children) {
         subChildren = getChildrenProperties(data, c);
         for (let sb of subChildren) {
            children.push(sb);
         }
      }
   }
   return children;
}

function hasChildrenProperties(property) {
   for (let p of ALL_DATA.metrics) {
      if (p.parent == property.name) {
         return true;
      }
   }
   for (let p of ALL_DATA.analysis) {
      if (p.parent == property.name) {
         return true;
      }
   }
   return false;
}

function calculateMaxLevel(data) {
   return Math.max.apply(Math, data.map(function (d) {
      return parseInt(d.level, 10);
   }))
}

/**
 * 
 * @param {Array} data Dataset.
 * @returns Maximum width for a property's name in the dataset.
 */
function calculateMaxNameWidth(data) {
   return Math.max.apply(Math, data.map(function (d) {
      return textSize(d.name, PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE).width;
   }))
}

/**
 * 
 * @param {Array} data Dataset.
 * @returns Maximum width for a property's value in the dataset.
 */
function calculateMaxValueWidth(data) {
   return Math.max.apply(Math, data.map(function (d) {
      return textSize(String(get_value(d)), VALUES_FONT_FAMILY, VALUES_FONT_SIZE).width;
   }))
}

/**
 * 
 * @param {Array} data Dataset.
 * @returns Maximum width for a property's ratio in the dataset.
 */
function calculateMaxRatioWidth(data) {
   return Math.max.apply(Math, data.map(function (d) {
      return textSize(String(get_ratio(d)), VALUES_FONT_FAMILY, VALUES_FONT_SIZE).width;
   }))
}

/**
 * 
 * @param {Array} data Dataset.
 * @returns Maximum width for a property's indentation in the dataset.
 */
function calculateMaxIndentationWidth(data) {
   return Math.max.apply(Math, data.map(function (d) {
      return textSize("-".repeat(1 + PROPERTY_INDENTATION * parseInt(d.level, 10)), PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE).width;
   }))
}

function filterData(data) {
   metrics = data.metrics;
   analysis = data.analysis;
   metrics = metrics.filter(function (d, i) { return VISIBLE_PROPERTIES[d.name]; });
   analysis = analysis.filter(function (d, i) { return VISIBLE_PROPERTIES[d.name]; });
   return { "metadata": data.metadata, "metrics": metrics, "analysis": analysis };
}

function redrawLabel(data) {
   var height = 0;
   updateProperties(data.metrics, "metrics");
   height = yMetrics + PROPERTY_HEIGHT * data.metrics.length;
   drawRule("rule2", height);
   height += MAIN_RULE_HEIGHT;
   d3.select("#analysis").attr("transform", "translate(0," + height + ")")
   updateProperties(data.analysis, "analysis");
   height += MARGING_BETWEEN_PROPERTIES + PROPERTY_HEIGHT * data.analysis.length;
   drawBorders(maxWidth, height);
   d3.select("chart").attr("height", height);
}
/**
 * Set-up the collapse zero values option.
 */
function collapseZeroValues(data) {
   var newData = filterData(data);
   redrawLabel(newData);
}

function collapseSubProperties(data) {
    for (let p of data.metrics) {
        var children = getChildrenProperties(data.metrics, p, true);
        for (let c of children) { VISIBLE_PROPERTIES[c.name] = false; }
        var children = getChildrenProperties(data.analysis, p, true);
        for (let c of children) { VISIBLE_PROPERTIES[c.name] = false; }
    }
    for (let p of data.analysis) {
        var children = getChildrenProperties(data.metrics, p, true);
        for (let c of children) { VISIBLE_PROPERTIES[c.name] = false; }
        var children = getChildrenProperties(data.analysis, p, true);
        for (let c of children) { VISIBLE_PROPERTIES[c.name] = false; }
    }
   newData = filterData(data);
   redrawLabel(newData);
}

function collapseProperty(data, property) {
   var children = getChildrenProperties(data.metrics, property, true);
   for (let c of children) { VISIBLE_PROPERTIES[c.name] = false; }
   var children = getChildrenProperties(data.analysis, property, true);
   for (let c of children) { VISIBLE_PROPERTIES[c.name] = false; }
   newData = filterData(data);
   redrawLabel(newData);
}

function expandProperty(data, property) {
   var children = getChildrenProperties(data.metrics, property, false);
   for (let c of children) { VISIBLE_PROPERTIES[c.name] = true; }
   var children = getChildrenProperties(data.analysis, property, false);
   for (let c of children) { VISIBLE_PROPERTIES[c.name] = true; }
   newData = filterData(data);
   redrawLabel(newData);
}

function drawSecondaryRules(data) {
   if (get_property_in_data(data, 'Compound features') !== null) drawSecondaryRule("Compound features");
   if (get_property_in_data(data, 'Root feature') !== null) drawSecondaryRule("Root feature");
   if (get_property_in_data(data, 'Features in constraints') !== null) drawSecondaryRule("Features in constraints");
}

function drawSecondaryRule(propertyName) {
   var property = d3.select("g[id='" + propertyName + "']");
   property.append("rect")
   .attr("x", property.select("#propertyName").attr("x"))
   .attr("y", 1)
   .attr("height", SECONDARY_RULE_HEIGHT)
   .attr("width", maxWidth - property.select("#propertyName").attr("x"));
}

/* End of Fact Label code */

function viewFactLabel(fileId) {
   fetch(`/factlabel/view/${fileId}`)
      .then(response => response.json())
      .then(data => {
            //document.getElementById('factlabelButton').href = `/factlabel/view/${fileId}`;
            var modal = new bootstrap.Modal(document.getElementById('factlabelViewerModal'));
            modal.show();
            console.log("Data");
            console.log(data)
            drawFMFactLabel(data['content']);
      })
      .catch(error => console.error('Error loading fact label:', error));
}

function showLoading() {
   document.getElementById("loading").style.display = "initial";
}

function hideLoading() {
   document.getElementById("loading").style.display = "none";
}


function copyToClipboard() {
   const text = document.getElementById('fileContent').textContent;
   navigator.clipboard.writeText(text).then(() => {
      console.log('Text copied to clipboard');
   }).catch(err => {
      console.error('Failed to copy text: ', err);
   });
}


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

window.drawFMFactLabel = drawFMFactLabel;