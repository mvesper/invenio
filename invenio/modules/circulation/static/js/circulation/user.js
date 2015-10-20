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
    $('.user_action').on('click', function(event){
        var elem = $(this);
        var type = elem.attr('data-type');
        var user_id = elem.attr('data-user_id');
        var item_id = elem.attr('id').split('_')[2];
        var clc_id = elem.attr('data-clc_id');
        var action = elem.attr('id').split('_')[0];
        var start_date = $('#circulation_date_from').val();
        var end_date = $('#circulation_date_to').val();
        
        var search_body = {'type': type,
                           'user_id': user_id,
                           'item_id': item_id,
                           'clc_id': clc_id,
                           'action': action,
                           'start_date': start_date,
                           'end_date': end_date}

        function success(data){
            window.location.reload();
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/user/run_action",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: success,
            contentType: 'application/json',
        });
    });

    function get_entity_id(){
        var url_parts = document.URL.split('/');
        return [url_parts[url_parts.length -2],
                url_parts[url_parts.length -1]];
    }

    $('#entity_detail').ready(function() {
        if ($('#entity_detail').length == 0) {
            return;
        }
        var data = get_entity_id();
        entity = data[0];
        id = data[1];

        function start_json_editor(data) {
            data = JSON.parse(data);
            json_editor = new JSONEditor($('#entity_detail')[0], 
                    {
                        schema: data['schema'],
                        theme: 'bootstrap3',
                        no_additional_properties: true,
                    });

            json_editor.setValue(data['data']);
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/get",
            data: JSON.stringify(JSON.stringify({'entity': entity, 'id': id})),
            success: start_json_editor,
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
