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
                    var current_state = tmp.splice(0, 5);
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

    function build_state_string(circulation_state, from, to, search) {
        return circulation_state.items.join(',') + ':' +
               circulation_state.users.join(',') + ':' +
               circulation_state.records.join(',') + ':' +
               from + ':' +
               to + ':' +
               search;
    }

    $('#circulation_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var search = $('#circulation_search').val();
            var from = $('#circulation_date_from').val();
            var to = $('#circulation_date_to').val();
            var circulation_state = get_circulation_state();

            var state_string = build_state_string(circulation_state, from, to, search);

            window.location.href = '/circulation/circulation/' + encodeURIComponent(state_string);
        }
    });

    $('#circulation_search_result').on("click", ".entity_delete", function(event){
        var entity = event.target.id.split('_')[1];
        var id = event.target.id.split('_')[2];
        var from = $('#circulation_date_from').val();
        var to = $('#circulation_date_to').val();

        var circulation_state = get_circulation_state();
        circulation_state[entity+'s'].splice(circulation_state[entity+'s'].indexOf(id), 1);

        var state_string = build_state_string(circulation_state, from, to, '');

        window.location.href = '/circulation/circulation/' + encodeURIComponent(state_string);
    });

    $('#circulation_validation').on("click", ".btn", function(event){
        var action = event.target.id.split('_')[0];
        var circulation_state = get_circulation_state();

        var from = $('#circulation_date_from').val();
        var to = $('#circulation_date_to').val();
        var state_string = build_state_string(circulation_state, from, to, '');
        
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

    $(document).ready(function(){
        if($('#circulation_alert').length){
            function hide_circulation_alert(){
                $('#circulation_alert').fadeOut(1000);
            }
            setTimeout(hide_circulation_alert, 5000);
        }
    });

    $('#circulation_date_from').datepicker({ dateFormat: 'yy-mm-dd' });
    $('#circulation_date_to').datepicker({ dateFormat: 'yy-mm-dd' });
}
);
