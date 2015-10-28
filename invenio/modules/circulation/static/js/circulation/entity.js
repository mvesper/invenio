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

    function get_entity_id(){
        var url_parts = document.URL.split('/');
        return [url_parts[url_parts.length -2],
                url_parts[url_parts.length -1]];
    }

    function get_entity_from_url(){
        var url_parts = document.URL.split('/');

        var part = null;
        for (var i=0; i < url_parts.length; i++){
            part = url_parts[i];
            if (part == 'entities') {
                return url_parts[i+1];
            }
        }
    }

    $('#entity_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var search_string = $('#entity_search').val();
            var url_encode = encodeURIComponent(search_string);
            var entity = $(this).attr('data-entity'); 

            window.location.href = '/circulation/entities/action/search/'+entity+'/'+url_encode;
        }
    });

    $('#entity_new').on("click", function(event){
        var entity = $(this).attr('data-entity');
        window.location.href = '/circulation/entities/action/create/'+entity;
    });

    var json_editor = null;

    $('#entity_create').on("click", function(event){
        var entity = $(this).attr('data-entity');
        var json = json_editor.getValue();

        var search_body = {'entity': entity, 'data': json}

        function success(data) {
            window.location.href = '/circulation/entities/' + entity;
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/create",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: success,
            contentType: 'application/json',
        });
    });
    
    $('#entity_update').on("click", function(event){
        var data = get_entity_id();
        var entity = data[0];
        var id = data[1];
        var json = json_editor.getValue();

        var search_body = {'entity': entity, 'id': id, 'data': json}

        function success(data) {
            window.location.reload();
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/update",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: success,
            contentType: 'application/json',
        });
    });

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
        if (Object.keys(data).length != 0){
            json_editor.setValue(data);
        }
    });

    $('#entity_actions').on("click", function(event){
        var data = get_entity_id();
        var entity = data[0];
        var id = data[1];
        var func = event.target.id;

        function success(data) {
            $(document).scrollTop(0);
            window.location.reload();
        }

        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/run_action",
            data: JSON.stringify(JSON.stringify({'entity': entity, 'id': id, 'function': func})),
            success: success,
            contentType: 'application/json',
        });
    });
    

    $('#entity_search_result').on("click", ".entity_delete", function(event){
        var decision = confirm('Do you really want to delete this entity?');
        if (!decision){
            return;
        }

        var entity = $('#entity_search_result').attr('data-entity');
        var id = event.target.id.split('_')[1];
        var element = $('#'+entity+'_'+id);

        function success(data) {
            window.location.reload();
        }

        var search_body = {'entity': entity, 'id': id};
        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/delete",
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
}
);
