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
    $('#entity_detail').ready(function() {
        if ($('#entity_detail').length == 0) {
            return;
        }
        var editor = $('#entity_detail');
        var data = JSON.parse(editor.attr('data-editor_data'));
        var schema = JSON.parse(editor.attr('data-editor_schema'));

        json_editor = new JSONEditor($('#entity_detail')[0], 
                {
                    schema: schema,
                    theme: 'bootstrap3',
                    no_additional_properties: true,
                });
        json_editor.setValue(data);
    });

    $('#ill_request_submit').on('click', function(){
        function get_form_data(element) {
            var data = {};
            $(element).find('.form-control').each(function(i, elem){
                elem = $(elem);
                var tmp = elem.attr('id').split('_');
                tmp.splice(0, 1);
                var field = tmp.join('_');
                data[field] = elem.val();
            });
            return data
        }

        var user_id = $('#ill_document').data('user_id');
        var record_id = $('#ill_document').data('record_id');
        var start_date = $('#ill_date_from').val();
        var end_date = $('#ill_date_to').val();
        var comments = $('#request_comments').val();
        var delivery = $('#circulation_option_delivery').val();

        var record = get_form_data('#document_form');

        record['record_id'] = record_id;

        var search_body = {user_id: user_id,
                           record: record,
                           start_date: start_date,
                           end_date: end_date,
                           comments: comments,
                           delivery: delivery};

        function success() {
            location.reload()
            //window.location.href = '/circulation/ill/request_ill/' + user_id + '/' + record_id;
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/ill/create_ill_request",
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

    $('.ill_list_action').on('click', function(event) {
        var data = $(event.target).data();

        function success() {
            location.reload()
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/ill/perform_action",
            data: JSON.stringify(JSON.stringify(data)),
            success: success,
            contentType: 'application/json',
        });
    });

    $('#ill_date_from').datepicker({ dateFormat: 'yy-mm-dd' });
    $('#ill_date_to').datepicker({ dateFormat: 'yy-mm-dd' });
}
);
