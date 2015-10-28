/*
 * This file is part of Invenio.
 * Copyright (C) 2015 CERN.
 *
 * Invenio is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * Invenio is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Invenio; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
 */

define(
    [
        'jquery',
    ],
function($) {
    function get_circulation_state() {
        var url_parts = document.URL.split('/');

        var part = null;
        for (var i=0; i < url_parts.length; i++){
            part = url_parts[i];
            if (part == 'circulation') {
                try {
                    var state = decodeURIComponent(url_parts[i+2]);
                    var tmp = state.split(':');
                    var current_state = tmp.splice(0, 7);
                    return {items: current_state[0].split(','),
                            users: current_state[1].split(','),
                            records: current_state[2].split(',')}
                } catch(err) {
                    return {items: [], users: [], records: []}
                }
            }
        }
        return part;
    }

    function build_state_string(circulation_state, from, to, waitlist, delivery, search) {
        return circulation_state.items.join(',') + ':' +
               circulation_state.users.join(',') + ':' +
               circulation_state.records.join(',') + ':' +
               from + ':' +
               to + ':' +
               waitlist + ':' +
               delivery + ':' +
               search;
    }

    $('#circulation_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var search = $('#circulation_search').val();
            var from = $('#circulation_date_from').val();
            var to = $('#circulation_date_to').val();
            var waitlist = $('#circulation_option_waitlist').is(':checked');
            var delivery = $('#circulation_option_delivery').val();
            var circulation_state = get_circulation_state();

            var state_string = build_state_string(circulation_state, from, to, waitlist, delivery, search);

            window.location.href = '/circulation/circulation/' + encodeURIComponent(state_string);
        }
    });

    $('#circulation_search_result').on("click", ".entity_delete", function(event){
        var entity = event.target.id.split('_')[1];
        var id = event.target.id.split('_')[2];
        var from = $('#circulation_date_from').val();
        var to = $('#circulation_date_to').val();
        var waitlist = $('#circulation_option_waitlist').is(':checked');
        var delivery = $('#circulation_option_delivery').val();

        var circulation_state = get_circulation_state();
        circulation_state[entity+'s'].splice(circulation_state[entity+'s'].indexOf(id), 1);

        var state_string = build_state_string(circulation_state, from, to, waitlist, delivery,  '');

        window.location.href = '/circulation/circulation/' + encodeURIComponent(state_string);
    });

    $('#circulation_validation').on("click", ".btn", function(event){
        var action = event.target.id.split('_')[0];
        var circulation_state = get_circulation_state();

        var from = $('#circulation_date_from').val();
        var to = $('#circulation_date_to').val();
        var waitlist = $('#circulation_option_waitlist').is(':checked');
        var delivery = $('#circulation_option_delivery').val();

        var state_string = build_state_string(circulation_state, from, to, waitlist, delivery, '');
        
        var search_body = {action: action,
                           circulation_state: state_string}

        function success(data) {
            window.location.href = '/circulation/';
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/circulation/run_action",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: success,
            contentType: 'application/json',
        });
    });

    var cal = null;

    $('#cal-heatmap').ready(function(){
        if ($('#cal-heatmap').length == 0) {
            return;
        }
        cal = new CalHeatMap();
        var data = JSON.parse($('#cal-heatmap').attr('data-cal_data'));
        var range = parseInt($('#cal-heatmap').attr('data-cal_range'));
        if (range == 0){
            return
        }
        var init = {itemSelector: "#cal-heatmap",
                    domain: "month",
                    subDomain: "x_day",
                    range: range,
                    data: data,
                    cellSize: 30,
                    subDomainTextFormat: "%d",
                    legend: [1],
                    legendColors: ["green", "#EE0000"],
                    displayLegend: false,}
        cal.init(init);
    });

    $(document).ready(function(){
        if($('#circulation_alert').length){
            function hide_circulation_alert(){
                $('#circulation_alert').fadeOut(1000);
            }
            setTimeout(hide_circulation_alert, 5000);
        }
    });

    $('.record_item').mouseenter(function(){
        var data = JSON.parse($(this).attr('data-cal_data'));
        var range = parseInt($(this).attr('data-cal_range'));
        if (range == 0){
            return
        }
        cal.update(data);
    });

    $('.record_item').mouseleave(function(){
        var data = JSON.parse($('#cal-heatmap').attr('data-cal_data'));
        var range = parseInt($('#cal-heatmap').attr('data-cal_range'));
        if (range == 0){
            return
        }
        cal.update(data);
    });

    $('.item_select').on('click', function(event){
        var record_id = $(this).attr('data-record_id');
        var item_id = $(this).attr('data-item_id');
        var state = get_circulation_state();

        //Remove record
        var i = state.records.indexOf(record_id);
        if (i != -1) {
            state.records.splice(i, 1);
        }

        //Add item
        //
        if (state.items.length == 1 && state.items.indexOf('') == 0) {
            state.items = [];
        }
        state.items.push(item_id);

        var from = $('#circulation_date_from').val();
        var to = $('#circulation_date_to').val();
        var waitlist = $('#circulation_option_waitlist').is(':checked');
        var delivery = $('#circulation_option_delivery').val();

        var state_string = build_state_string(state, from, to, waitlist, delivery, '');

        window.location.href = '/circulation/circulation/' + encodeURIComponent(state_string);
    });

    $('#circulation_option_waitlist').ready(function(){
        var obj = $('#circulation_option_waitlist');
        obj.attr('checked', (obj.attr('data-checked') === 'True'));
    });

    $('#circulation_option_delivery').ready(function(){
        var obj = $('#circulation_option_delivery');
        obj.val(obj.attr('data-val'));
    });

    $('#circulation_check_params').on('click', function(){
        var state = get_circulation_state();
        var from = $('#circulation_date_from').val();
        var to = $('#circulation_date_to').val();
        var waitlist = $('#circulation_option_waitlist').is(':checked');
        var delivery = $('#circulation_option_delivery').val();
        var state_string = build_state_string(state, from, to, waitlist, delivery, '');

        window.location.href = '/circulation/circulation/' + encodeURIComponent(state_string);
    });

    /*
    $('#validation_annotations').ready(function(){
        var data = JSON.parse($('#validation_annotations').attr('data-validation'));

        var elems = {date: '#circulation_dates',
                     item: '#circulation_items'};
        var mapping = {start_date: 'date', date_suggestion: 'date',
                       items_status: 'item'}

        var res = {};
        for (var key in data) {
            if (data.hasOwnProperty(key)) {
                var values = data[key];
                for (var i = 0; i < values.length; i++){
                    var category = mapping[values[i][0]];
                    var msg = values[i][1];
                    if (elems.hasOwnProperty(category)){
                        elem = elems[category];
                        try {
                            res[elem].push([key, msg]);
                        } catch(err) {
                            res[elem] = [[key, msg]];
                        }
                    }
                }
            }
        }

        for (var key in res) {
            if (res.hasOwnProperty(key)) {
                var values = res[key];
                var content = [];
                for (var i = 0; i < values.length; i++) {
                    var val = values[i];
                    var msg = val[0] + ': ' + val[1];
                    content.push(msg);
                }

                $(key).popover({
                    placement:'right',
                    trigger:'manual',
                    html:true,
                    container:'body',
                    content:content.join('<br>')}).popover('show');
            }
        }

        $('#circulation_validation').popover({
            placement:'bottom',
            trigger:'hover',
            html:true,
            content:data.loan});
    });
    */

    $('#circulation_date_from').datepicker({ dateFormat: 'yy-mm-dd' });
    $('#circulation_date_to').datepicker({ dateFormat: 'yy-mm-dd' });
}
);
