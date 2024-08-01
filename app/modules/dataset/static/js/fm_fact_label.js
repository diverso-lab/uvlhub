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
   PROPERTY_HEIGHT = textSize("Any text", PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE, "bold").height;// + MARGING_BETWEEN_PROPERTIES;
   maxIndentationWidth = Math.max(calculateMaxIndentationWidth(data.metrics), calculateMaxIndentationWidth(data.analysis));
   maxNameWidth = Math.max(calculateMaxNameWidth(data.metrics), calculateMaxNameWidth(data.analysis));
   maxValueWidth = Math.max(calculateMaxValueWidth(data.metrics), calculateMaxValueWidth(data.analysis));
   maxRatioWidth = Math.max(calculateMaxRatioWidth(data.metrics), calculateMaxRatioWidth(data.analysis));
   maxWidth = maxIndentationWidth + maxNameWidth + PROPERTIES_VALUES_SPACE + maxValueWidth + PROPERTIES_RATIO_SPACE + maxRatioWidth + LEFT_MARGING; //textSize("-".repeat(PROPERTY_INDENTATION), PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE).width;
   chart.attr("width", maxWidth);
   //.attr("height", BAR_HEIGHT * 10 + BAR_HEIGHT * data.metadata.length + BAR_HEIGHT * data.metrics.length); // CAMBIAR EL *10 AJUSTANDOLO BIEN

   x = d3.scaleLinear().domain([0, maxWidth]).range([0, maxWidth]);

   // Title
   var titleSize = textSize(get_property(data, "Name").value, TITLE_FONT_FAMILY, TITLE_FONT_SIZE);
   var yTitle = TOP_MARGING;
   var title = chart.append("g").attr("transform", "translate(0," + yTitle + ")");
   title.append("text")
      .text(get_property(data, 'Name').value)
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
      .text(get_property(data, 'Description').value)
      .attr("x", function (d) { return x(indentationDescription) })
      //.attr("y", BAR_HEIGHT / 2)
      .attr("font-family", DESCRIPTION_FONT_FAMILY)
      .attr("font-size", DESCRIPTION_FONT_SIZE)
      .call(wrap, maxWidth - indentationDescription);
   var descriptionSize = description.node().getBBox();

   // Keywords
   var keywordHeight = yDescription + descriptionSize.height + 1;
   if (get_property(data, 'Tags').value === null) {
      var keywordsSize = descriptionSize;
   } else {
      var keywords = chart.append("g").attr("transform", "translate(0," + keywordHeight + ")");
      addMetadata(keywords, "Tags:", get_property(data, 'Tags').value);
      var keywordsSize = keywords.node().getBBox();
   }

   // Author
   var authorHeight = keywordHeight + keywordsSize.height;
   if (get_property(data, 'Author').value === null) {
      var authorSize = { "width": 0, "height": 0 };
   } else {
      var author = chart.append("g").attr("transform", "translate(0," + authorHeight + ")");
      addMetadata(author, "Author:", get_property(data, 'Author').value);
      var authorSize = author.node().getBBox();
   }

   // Year
   var yearHeight = authorHeight + authorSize.height;
   if (get_property(data, 'Year').value === null) {
      var yearSize = { "width": 0, "height": 0 };
   } else {
      var year = chart.append("g").attr("transform", "translate(0," + yearHeight + ")");
      addMetadata(year, "Year:", get_property(data, 'Year').value);
      var yearSize = year.node().getBBox();
   }

   // Domain
   var domainHeight = yearHeight + yearSize.height;
   if (get_property(data, 'Domain').value === null) {
      var domainSize = { "width": 0, "height": 0 };
   } else {
      var domain = chart.append("g").attr("transform", "translate(0," + domainHeight + ")");
      addMetadata(domain, "Domain:", get_property(data, 'Domain').value);
      var domainSize = domain.node().getBBox();
   }

   // Reference
   if (!get_property(data, 'Reference').value == "") {
      var reference = chart.append("g").attr("transform", "translate(0," + (domainHeight + domainSize.height - MAIN_RULE_HEIGHT - 10) + ")");
      reference.append('a')
         .attr("id", "hrefIcon")
         .attr("href", get_property(data, 'Reference').value)
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

   chart.attr("height", maxHeight);

   // Set the configuration options
   d3.select("#collapseZeroValues").on("change", function () { collapseZeroValues(data); });
   d3.select("#collapseSubProperties").on("change", function () { collapseSubProperties(data); });
   //d3.selectAll("#collapse").on("click", function (d) { collapseProperty(data, d); });
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
                  tooltip.html(d.description)
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
                  contentDetail.html(d.value)
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
   return d.size === null ? d.value : d.size;
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
   if (d3.select("#collapseZeroValues").property("checked")) {
      metrics = metrics.filter(function (d, i) { return get_value(d) != '0'; });
      analysis = analysis.filter(function (d, i) { return get_value(d) != '0'; });
   }
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
   if (d3.select("#collapseSubProperties").property("checked")) {
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
   } else {
      for (let p of data.metrics) {
         var children = getChildrenProperties(data.metrics, p, true);
         for (let c of children) { VISIBLE_PROPERTIES[c.name] = true; }
         var children = getChildrenProperties(data.analysis, p, true);
         for (let c of children) { VISIBLE_PROPERTIES[c.name] = true; }
      }
      for (let p of data.analysis) {
         var children = getChildrenProperties(data.metrics, p, true);
         for (let c of children) { VISIBLE_PROPERTIES[c.name] = true; }
         var children = getChildrenProperties(data.analysis, p, true);
         for (let c of children) { VISIBLE_PROPERTIES[c.name] = true; }
      }
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
   
   // var translate = d3.select("g[id='Compound features']").node() // get the node
   //    .transform          // get the animated transform list
   //    .baseVal            // get its base value
   //    .getItem(0)         // get the first transformation from the list, i.e. your translate
   //    .matrix             // get the matrix containing the values

   // // console.log(`Translate x: ${translate.e}, y: ${translate.f}`);

   // var property = d3.select("g[id='Compound features']");
   // //.append("g").attr("class", "secondaryRule").attr("transform", "translate(0," + translate.f - 3 + ")");
   // property.append("rect")
   // .attr("x", property.select("#propertyName").attr("x"))
   // .attr("y", 1)
   // .attr("height", SECONDARY_RULE_HEIGHT)
   // .attr("width", maxWidth - property.select("#propertyName").attr("x"));
}

function drawSecondaryRule(propertyName) {
   var property = d3.select("g[id='" + propertyName + "']");
   property.append("rect")
   .attr("x", property.select("#propertyName").attr("x"))
   .attr("y", 1)
   .attr("height", SECONDARY_RULE_HEIGHT)
   .attr("width", maxWidth - property.select("#propertyName").attr("x"));
}

// function calculateTotalMaxWidth(data) {
//    return Math.max.apply(Math, data.map(function(d) {
//       indentationWidth = textSize("-".repeat(1 + PROPERTY_INDENTATION * parseInt(d.level, 10)), PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE).width;
//       nameWidth = textSize(d.name, PROPERTY_FONT_FAMILY, PROPERTY_FONT_SIZE).width;
//       valueWidth = textSize(String(get_value(d)), VALUES_FONT_FAMILY, VALUES_FONT_SIZE).width;
//       ratioWidth = textSize(String(get_ratio(d)), VALUES_FONT_FAMILY, VALUES_FONT_SIZE).width;
//       return indentationWidth + nameWidth + valueWidth + ratioWidth;
//    })) + PROPERTIES_VALUES_SPACE + PROPERTIES_RATIO_SPACE + LEFT_MARGING;
// };
