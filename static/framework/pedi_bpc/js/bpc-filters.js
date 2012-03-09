// Filters and filter handlers for the BPC app
//
// Author: Nikolai Schwertner
//
// Revision history:
//       2011-06-27 Refactored code
//     2011-05-19 Restructured filter loaders to reduce code duplication
//     2011-05-18 Initial split from main code

// Initialize the BPC global obeject as needed
var BPC;
if (!BPC) {
    BPC = {};
}

(function () {
    "use strict";

    /**
    * Event handler for the toggle filter buttons
    */
    BPC.updateFilters = function () {
        //BPC.disableControls ();
        BPC.loadFilterSettings ();
        BPC.redrawViewLong (BPC.patient,BPC.zones);
        BPC.redrawViewTable (BPC.patient);
        //BPC.enableControls ();
    };

    /**
    * Filter settings loader
    */
    BPC.loadFilterSettings = function () {
    
        var f = BPC.filterSettings;
        
        f.encounter = [];
        f.site = [];
        f.position = [];
        f.method = [];
        
        if ($("#chkFilterInpatient").attr("checked")) {
            f.encounter.push("Inpatient");
        }
        if ($("#chkFilterAmbulatory").attr("checked")) {
            f.encounter.push("Ambulatory");
        }
        if ($("#chkFilterArm").attr("checked")) {
            f.site.push("Arm");
        }
        if ($("#chkFilterLeg").attr("checked")) {
            f.site.push("Leg");
        }
        if ($("#chkFilterSitting").attr("checked")) {
            f.position.push("Sitting");
        }
        if ($("#chkFilterStanding").attr("checked")) {
            f.position.push("Standing");
        }
        if ($("#chkFilterAuscultation").attr("checked")) {
            f.method.push("Auscultation");
        }
        if ($("#chkFilterMachine").attr("checked")) {
            f.method.push("Machine");
        }
    };

    /**
    * Event handler for the date range slider
    *
    * @param {Integer} valueFrom The from value of the slider (0-100)
    * @param {Integer} valueTo The to value of the slider (0-100)
    */
    BPC.updateDateRange = function (valueFrom,valueTo) {
        BPC.setDateRange (valueFrom,valueTo);
        BPC.redrawViewLong (BPC.patient,BPC.zones);
        BPC.redrawViewTable (BPC.patient);

    };

    /**
    * Updates the slider label and filter settings
    *
    * @param {Integer} valueFrom The from value of the slider (0-100)
    * @param {Integer} valueTo The to value of the slider (0-100)
    */
    BPC.setDateRange = function (valueFrom, valueTo) {

        var s = BPC.getViewSettings (),
            startTime = BPC.patient.startUnixTime,
            endTime = BPC.patient.endUnixTime,
            fromTime,
            toTime;
            
        // Convert the slider values to unix dates
        fromTime = BPC.scale (valueFrom, 0, 100, startTime, endTime);
        toTime = BPC.scale (valueTo, 0, 100, startTime, endTime);
        
        // Convert the values to the standard format and update the settings
        BPC.filterSettings.dateFrom = parse_date(fromTime).toString('yyyy-MM-dd');
        BPC.filterSettings.dateTo = parse_date(toTime).toString('yyyy-MM-dd');
        
        // Convert the slider range dates to the display format
        fromTime = parse_date(fromTime).toString(s.dateFormat);
        toTime = parse_date(toTime).toString(s.dateFormat);
        
        // Update the slider label
        $( "#label-timerange" ).text( fromTime + " - " + toTime );
    };
    
    /**
    * Utility for checking of the presence of a value within a list of values
    *
    * @param {String} value The target value to be searched for
    * @param {String Array} values The list of values to be searched through
    *
    * @returns {Boolean} True if the value was found in the list of values
    */
    var inList = function (value, values) {
        var i;
        
        for (i = 0; i < values.length; i++) {
            if (value === values[i]) {
                return true;
            }
        }
        
        return false;
    };

    /**
    * Filter plugin functions for the various toggle filters (undefined values fall through the filters)
    *
    * @param {Object} record The patient data record to be processed
    *
    * @returns {Boolean} True if the patient data record is allowed through the filter
    */
    BPC.filterEncounter = function (record) {
        return !record.encounter || inList (record.encounter, BPC.filterSettings.encounter);
    };
        
    BPC.filterSite = function (record) {
        var site;
        
        if (!record.site) {
            return true;
        }
        
        site = record.site.toLowerCase();
        
        if (site.indexOf("arm") !== -1) {
            return inList ("Arm", BPC.filterSettings.site);
        } else if (site.indexOf("leg") !== -1) {
            return inList ("Leg", BPC.filterSettings.site);
        } else {
            return false;
        }
    };
        
    BPC.filterPosition = function (record) {
        return !record.position || inList (record.position, BPC.filterSettings.position);
    };

    BPC.filterMethod = function (record) {
        return !record.method || inList (record.method, BPC.filterSettings.method);
    };

    BPC.filterValid = function (record) {
        return record.sPercentile && record.dPercentile;
    };

    BPC.filterPediatric = function (record) {
        return record.age < BPC.ADULT_AGE;
    };

    /**
    * Filter plugin functions for the date range filters
    *
    * @param {Object} record The patient data record to be processed
    *
    * @returns {Boolean} True if the patient data record is allowed through the filter
    */
    BPC.filterDate = function (record) {
        var date = parse_date(record.unixTime).toString('yyyy-MM-dd');
        return BPC.filterSettings.dateFrom <= date && date <= BPC.filterSettings.dateTo;
    };

    /**
    * Linear scaling function mapping a point X from the domain [x1,x2] to the range [y1,y2]
    *
    * @param {Number} X
    * @param {Number} x1
    * @param {Number} x2
    * @param {Number} y1
    * @param {Number} y2
    *
    * @returns {Number}
    */
    BPC.scale = function (X, x1, x2, y1, y2) {
        var a, b;
        
        if (x1 === x2) {
            return y1 + (y2-y1)/2;
        }
        
        a = (y2-y1)/(x2-x1);
        b = y1 - a*x1;
        
        //console.log ("scale: " + X + " " + x1 + " " + x2 + " " + y1 + " " + y2 + " -> " + (a*X + b));
        
        return a*X + b;
    };

    /**
    * Method for applying all filters to a patient object
    *
    * @returns {Object} A new patient object resulting from the filters application. The original
                        object remains unaltered.
    */
    BPC.Patient.prototype.applyFilters = function (patient) {
        return this.applyFilter(BPC.filterSite)
				   .applyFilter(BPC.filterPosition)
				   .applyFilter(BPC.filterDate)
				   .applyFilter(BPC.filterMethod);
				   //.applyFilter(BPC.filterPediatric)
                   //.applyFilter(BPC.filterEncounter)
    };
}());