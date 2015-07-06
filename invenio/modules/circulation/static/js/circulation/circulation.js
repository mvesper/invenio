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
        'hgn!js/circulation/templates/entity',
    ],
function($, entity_template) {

    function get_entity(){
        var url_parts = document.URL.split('/');
        return url_parts[url_parts.length -1];
    }

    function get_entity_id(){
        var url_parts = document.URL.split('/');
        return [url_parts[url_parts.length -2],
                url_parts[url_parts.length -1]];
    }

    function prepare_entities_for_display(data){
        var res = [];
        for(var i = 0; i < data.length; i++){
            var obj = data[i];
            var tmp = {'id': obj.id, 'attributes': []};
            for (var key in obj) {
                if (key != 'methods') {
                    tmp.attributes.push({'key': key, 'value': obj[key]});
                }
            }
            res.push(tmp);
        }

        return res;
    }

    function action_validate_result(data){
        $('#circulation_validation').show();
    }

    var library = [];
    var user = [];
    var item = [];

    function populate_circulation_search(data){
        try{
            data = JSON.parse(data);
            library = library.concat(prepare_entities_for_display(data.library));
            user = user.concat(prepare_entities_for_display(data.user));
            item = item.concat(prepare_entities_for_display(data.items));
        } catch(error) {}

        $('#circulation_library').html(entity_template({'type': 'library',
                                                        'entities': library}));
        $('#circulation_user').html(entity_template({'type': 'library',
                                                     'entities': user}));
        $('#circulation_item').html(entity_template({'type': 'library',
                                                     'entities': item}));

        var search_body = {'user': user,
                           'items': item,
                           'library': library,
                           'start_date': $('#circulation_date_from').val(),
                           'end_date': $('#circulation_date_to').val()}

        $.ajax({
            type: "POST",
            url: "/circulation/api/circulation/try_actions",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: action_validate_result,
            contentType: 'application/json',
        });
    }

    $('#circulation_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var search_body = {'search': {}}

            var search = $('#circulation_search').val();
            var search_parts = search.split(' ');

            for(var i = 0; i < search_parts.length; i++){
                try {
                    var search_part = search_parts[i];
                    var splited = search_part.split('=');
                    var key = splited[0].replace(' ', '');
                    var value = splited[1].replace(' ', '');
                    search_body.search[key] = value;
                } catch (err) {}
            }

            $.ajax({
                type: "POST",
                url: "/circulation/api/circulation/search",
                data: JSON.stringify(JSON.stringify(search_body)),
                success: populate_circulation_search,
                contentType: 'application/json',
            });
        }
    });


    function populate_entity_search(data){
        data = JSON.parse(data);

        var res = [];
        for(var i = 0; i < data.length; i++){
            var obj = data[i];
            var tmp = {'id': obj.id, 'attributes': []};
            for (var key in obj) {
                if (key != 'methods') {
                    tmp.attributes.push({'key': key, 'value': obj[key]});
                }
            }
            res.push(tmp);
        }

        var url_parts = document.URL.split('/');
        var type = url_parts[url_parts.length -1];
        $('#entity_search_result').html(entity_template({'type': type,
                                                         'entities': res}));
    };

    $('#entity_search').on("keydown", function(event){
        if (event.keyCode == 13) {
            var url_parts = document.URL.split('/');
            var entity = url_parts[url_parts.length -1];

            var search_body = {'entity': entity, 'search': {}}

            var search = $('#entity_search').val();
            var search_parts = search.split(' ');

            for(var i = 0; i < search_parts.length; i++){
                try {
                    var search_part = search_parts[i];
                    var splited = search_part.split('=');
                    var key = splited[0].replace(' ', '');
                    var value = splited[1].replace(' ', '');
                    search_body.search[key] = value;
                } catch (err) {}
            }

            $.ajax({
                type: "POST",
                url: "/circulation/api/entity/search",
                data: JSON.stringify(JSON.stringify(search_body)),
                success: populate_entity_search,
                contentType: 'application/json',
            });
        }
    });
    
    $('#entity_new').on("click", function(event){
        var entity = get_entity();
        window.location.href = '/circulation/entities/create/' + entity;
    });


    $('#entity_create').on("click", function(event){
        var entity = get_entity();
        var json = $("#entities_json_editor").val();

        var search_body = {'entity': entity, 'data': json}
        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/create",
            data: JSON.stringify(JSON.stringify(search_body)),
            contentType: 'application/json',
        });
    });

    $('#entity_update').on("click", function(event){
        var tmp = get_entity_id();
        var entity = tmp[0];
        var id = tmp[1];
        var json = $("#entities_json_editor").val();

        var search_body = {'entity': entity, 'id': id, 'data': json}
        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/update",
            data: JSON.stringify(JSON.stringify(search_body)),
            contentType: 'application/json',
        });
    });

    $('#entity_search_result').on("click", ".entity_delete", function(event){
        var entity = get_entity();
        var id = event.target.id.split('_')[2];

        var search_body = {'entity': entity, 'id': id};

        var element = $('#entity_'+id);
        //element.hide(500, function(){element.remove();});
        $.ajax({
            type: "POST",
            url: "/circulation/api/entity/delete",
            data: JSON.stringify(JSON.stringify(search_body)),
            success: element.hide(500, function(){element.remove();}),
            contentType: 'application/json',
        });
    });

    $('#circulation_search_result').on("click", ".entity_delete", function(event){
        var id = event.target.id.split('_')[1];
        var parentElement = event.target.parentNode;
        while(!parentElement.id.lastIndexOf('circulation', 0) == 0){
            parentElement = parentElement.parentElement;

        }
        var kind = parentElement.id.split('_')[1];
        var list = null;
        if (kind == 'item') {
            list = item;
        }
        if (kind == 'library') {
            list = library;
        }
        if (kind == 'user') {
            list = user;
        }

        var i = 0;
        for (i = 0; i < list.length; i++){
            var tmp = list[i];
            if (tmp.id == id){
                break;
            }
        }

        list.splice(i, 1);
        populate_circulation_search({});
    });

    $('#circulation_date_from').datepicker();
    $('#circulation_date_to').datepicker();
}
);
