import {pushData} from "../session";

const tpl = `<div class="webio-datatable">
<div class="ag-theme-{{theme}} ag-grid" style="width: 100%; height: {{height}}">
    <div class="grid-loading">⌛️ Loading Datatable...</div>
</div>
<div class="ag-grid-cell-bar"></div>
<div class="ag-grid-tools">
    <div class="grid-status">
        <div class="select-count">Selected <span class="ag-grid-row-count">0</span> <span
                class="ag-grid-row-unit">row</span></div>
        <div class="grid-unselect" style="display: flex;align-items: center;">
            <div class="sep"></div>
            <div class="act-btn">Unselect</div>
        </div>
    </div>
    <div class="grid-actions"></div>
</div>
</div>`

function path2field(path: string[]) {
    return [
        path.join(''),
        path.map((p) => p.length).join('_'),
        path.length
    ].join('_');
}

function field2path(field: string) {
    let parts = field.split('_');
    let level = parseInt(parts[parts.length - 1]);
    let path = [];
    let start = 0;
    for (let i = 0; i < level; i++) {
        let len = parseInt(parts[parts.length - 1 - level + i]);
        path.push(field.substring(start, start + len));
        start += len;
    }
    return path;
}

function flatten_row_and_extract_column(
    row: { [field: string]: any },  // origin row
    current_columns: { [field: string]: any },  // used to receive column struct
    row_data: { [field: string]: any }, // used to receive flatten row
    path: string[]
) {
    if (!row) return;
    let keys: string[] = [];
    try {
        keys = Object.keys(row);
    } catch (e) {
    }
    keys.forEach((key: any) => {
        let val = row[key];
        path.push(key);
        if (!(key in current_columns))
            current_columns[key] = {};
        if (val && typeof val == "object" && !Array.isArray(val)) {
            flatten_row_and_extract_column(val, current_columns[key], row_data, path);
        } else {
            row_data[path2field(path)] = val;
        }
        path.pop();
    });
}

function flatten_row(row: { [field: string]: any }) {
    let current_columns = {}, row_data = {}, path: string[] = [];
    flatten_row_and_extract_column(row, current_columns, row_data, path);
    return row_data;
}

/*
* field_args: key -> column_def
* path_args: [(path, column_def), ...]
* */
function row_data_and_column_def(
    data: any[],
    field_args: { [field: string]: any },
    path_args: any[][],
    column_order: { [field: string]: any },
) {
    function capitalizeFirstLetter(s: string) {
        return s.charAt(0).toUpperCase() + s.slice(1);
    }


    function gen_columns_def(
        current_columns: { [field: string]: any },  // all leaf node is {}
        path: string[],
        field_args: { [field: string]: any },
        path_field_args: { [field: string]: any },
        args_from_parent: { [field: string]: any }
    ) {
        let column_def: any[] = [];
        Object.keys(current_columns).forEach((key) => {
            let val = current_columns[key];
            path.push(key);
            let path_field = path2field(path);
            if (Object.keys(val).length > 0) {
                let extra_args = {
                    ...args_from_parent,
                    ...(path_field_args[path_field] || {}),
                };
                column_def.push({
                    headerName: capitalizeFirstLetter(key.replace(/_/g, " ")),
                    children: gen_columns_def(val, path, field_args, path_field_args, extra_args)
                });
            } else {
                let column = {
                    headerName: capitalizeFirstLetter(key.replace(/_/g, " ")),
                    field: path_field,
                    ...args_from_parent,
                    ...(field_args[key] || {}),
                    ...(path_field_args[path_field] || {}),
                };
                column_def.push(column);
            }
            path.pop();
        })
        return column_def;
    }

    let columns = {};
    let rows = [];
    for (let row of data) {
        let row_data = {};
        flatten_row_and_extract_column(row, columns, row_data, []);
        rows.push(row_data);
    }
    let path_field_args: { [field: string]: any } = {};
    path_args.map(([path, column_def]) => {
        path_field_args[path2field(path)] = column_def
    })

    if (column_order) {
        // replace all leaf node in column_order to {}
        columns = JSON.parse(
            JSON.stringify(column_order),
            (key, val) => (val && typeof val == "object" && !Array.isArray(val)) ? val : {}
        );

    }
    let column_defs = gen_columns_def(columns, [], field_args, path_field_args, {});
    return {
        rowData: rows,
        columnDefs: column_defs,
    }
}

function parse_js_func(object: any, js_func_key: string) {
    return JSON.parse(JSON.stringify(object), (key, value) => {
        if (
            typeof value === 'object' &&
            value.__pywebio_js_function__ === js_func_key &&
            'params' in value && 'body' in value
        ) {
            try {
                return new Function(...value.params, value.body);
            } catch (e) {
                console.error("Parse js function error: %s", e);
                return null;
            }
        }
        return value;
    })
}

function safe_run(func_name: string, func: any, ...args: any[]) {
    try {
        if (typeof func === 'function')
            func.bind(this)(...args);
    } catch (e) {
        console.error("Error on %s function:\n", func_name, e);
    }
}

const gridDefaultOptions = {
    //https://www.ag-grid.com/javascript-data-grid/row-selection/
    rowMultiSelectWithClick: true,
    groupSelectsChildren: true,
    groupSelectsFiltered: true,

    // https://www.ag-grid.com/javascript-data-grid/selection-overview/
    enableCellTextSelection: true,
    ensureDomOrder: true,

    autoGroupColumnDef: {
        pinned: 'left',//force pinned left. Does not work in columnDef
    },

    // some enterprise config
    enableCharts: true,
    enableRangeSelection: true,
    // animateRows: true, // have rows animate to new positions when sorted
    sideBar: {
        toolPanels: [
            {
                id: 'columns',
                labelDefault: 'Columns',
                labelKey: 'columns',
                iconKey: 'columns',
                toolPanel: 'agColumnsToolPanel',
                minWidth: 225,
                width: 290,
                maxWidth: 400,
            },
            {
                id: 'filters',
                labelDefault: 'Filters',
                labelKey: 'filters',
                iconKey: 'filter',
                toolPanel: 'agFiltersToolPanel',
                minWidth: 180,
                maxWidth: 400,
                width: 250,
            },
        ],
        position: 'right',
    },
};

const gridDefaultColDef = {
    //https://www.ag-grid.com/javascript-data-grid/row-height/#text-wrapping
    //wrapText: true,     // <-- HERE
    //autoHeight: true,   // <-- & HERE

    // suppressMenu: true,
    wrapHeaderText: true,
    autoHeaderHeight: true,

    sortable: true,
    filter: true,
    // flex: 1,
    // minWidth: 90,
    resizable: true,

    // allow every column to be aggregated
    enableValue: true,
    // allow every column to be grouped
    enableRowGroup: true,
    // allow every column to be pivoted
    enablePivot: true,
    // sizeColumnsToFit:true,
    defaultAggFunc: 'avg',
}


export let Datatable = {
    handle_type: 'datatable',
    get_element: function (spec: any): JQuery {
        let html = Mustache.render(tpl, spec);
        let elem = $(html);

        spec.field_args = parse_js_func(spec.field_args, spec.js_func_key);
        spec.path_args = parse_js_func(spec.path_args, spec.js_func_key);
        spec.grid_args = parse_js_func(spec.grid_args, spec.js_func_key);
        let auto_height = spec.height == 'auto';

        let options = row_data_and_column_def(spec.records, spec.field_args, spec.path_args, spec.column_order);

        if (spec.actions.length === 0) {
            elem.find('.ag-grid-tools').hide();
        } else {
            // not show actions at beginning
            elem.find('.ag-grid-tools .grid-unselect, .ag-grid-tools .grid-actions').hide();
        }

        let getRowId = undefined;
        if (spec.id_field) {
            getRowId = (params: any) => params.data[path2field(spec.id_field)]
        }

        let grid_resolve: (opts: any) => void = null;
        let gridPromise = new Promise((resolve, reject) => {
            grid_resolve = resolve;
        });
        if (spec.instance_id)
            // @ts-ignore
            window[`ag_grid_${spec.instance_id}_promise`] = gridPromise;

        const gridOptions: any = {
            ...gridDefaultOptions,
            ...spec.grid_args,

            path2field, field2path, spec, flatten_row,

            // https://www.ag-grid.com/javascript-data-grid/row-ids/
            getRowId: getRowId,

            rowData: options.rowData,
            columnDefs: options.columnDefs,

            //https://www.ag-grid.com/javascript-data-grid/row-selection/
            rowSelection: (spec.actions.length > 0) && (spec.multiple_select ? 'multiple' : 'single'),

            defaultColDef: {
                ...gridDefaultColDef,
                ...(spec.grid_args.defaultColDef || {}),
            },
            getSelectedRowIDs: function () {
                const selectedRows = gridOptions.api.getSelectedNodes();
                let selected_row_ids = [];
                for (let r of selectedRows) {
                    if (!r.group)
                        selected_row_ids.push(r.id);
                }
                if (!spec.id_field)
                    selected_row_ids = selected_row_ids.map((rid: any) => parseInt(rid));
                return selected_row_ids;
            },
            onGridReady: (param: any) => {
                grid_resolve(gridOptions);
                if (auto_height) {
                    gridOptions.api.setDomLayout('autoHeight');
                }

                let grid_elem = elem.find(".ag-grid")[0];
                let on_grid_show = Promise.resolve();
                if (grid_elem.clientWidth === 0) {  // the grid is hidden via `display: none`, wait for it to show
                    on_grid_show = new Promise((resolve) => {
                        // @ts-ignore
                        let observer = new ResizeObserver((entries, observer) => {
                            if (grid_elem.clientWidth > 0) {
                                observer.disconnect();
                                resolve();
                            }
                        });
                        observer.observe(grid_elem);
                    });
                }
                on_grid_show.then(() => {
                    gridOptions.columnApi.autoSizeAllColumns();
                    let content_width = 0;
                    gridOptions.columnApi.getColumns().forEach((column: any) => {
                        if (!column.getColDef().hide)
                            content_width += column.getActualWidth();
                    });
                    if (content_width < grid_elem.clientWidth) {
                        // the content is smaller than the grid, so we set columns to adjust in size to fit the grid horizontally
                        gridOptions.api.sizeColumnsToFit();
                    }
                })

                if (spec.actions.length > 0) {
                    elem.find('.ag-grid-tools').css('opacity', 1);
                }
                elem.find('.grid-unselect .act-btn').on('click', () => gridOptions.api.deselectAll());
                for (let btn_idx in spec.actions) {
                    let label = spec.actions[btn_idx];
                    if (label === null) {
                        elem.find('.grid-actions').append('<div class="sep"></div>');
                    } else {
                        let btn = $(`<div class="act-btn">${label}</div>`);
                        btn.on('click', () => {
                            pushData({
                                btn: parseInt(btn_idx),
                                rows: gridOptions.getSelectedRowIDs()
                            }, spec.callback_id)
                        });
                        elem.find('.grid-actions').append(btn);
                    }
                }

                safe_run('agGrid.onGridReady()', spec.grid_args.onGridReady, param);
            },
            onCellFocused: (params: any) => {
                var row = gridOptions.api.getDisplayedRowAtIndex(params.rowIndex);
                var cellValue = gridOptions.api.getValue(params.column, row)
                if (cellValue === undefined)
                    cellValue = ''
                document.querySelector('.ag-grid-cell-bar').innerHTML = cellValue;

                if (spec.cell_content_bar) {
                    let bar = elem.find('.ag-grid-cell-bar');
                    bar.show();
                }

                safe_run('agGrid.onCellFocused()', spec.grid_args.onCellFocused, params);
            },

            onSelectionChanged: (param: any) => {
                const selectedRows = gridOptions.getSelectedRowIDs();
                if (spec.on_select && selectedRows.length > 0) {
                    pushData({
                        rows: selectedRows
                    }, spec.callback_id)
                }

                elem.find(".ag-grid-row-count").text(selectedRows.length);
                elem.find(".ag-grid-row-unit").text(selectedRows.length > 1 ? 'rows' : 'row');
                if (selectedRows.length === 0) {
                    elem.find('.ag-grid-tools .grid-unselect, .ag-grid-tools .grid-actions').hide();
                }
                if (selectedRows.length >= 1) {
                    elem.find('.ag-grid-tools .grid-unselect, .ag-grid-tools .grid-actions').fadeIn(200);
                }

                safe_run('agGrid.onSelectionChanged()', spec.grid_args.onSelectionChanged, param);
            }
        };

        let ag_version = spec.enterprise_key ? 'ag-grid-enterprise' : 'ag-grid';
        // @ts-ignore
        requirejs([ag_version], function (agGrid) {
            elem.find('.grid-loading').remove();
            new agGrid.Grid(elem.find(".ag-grid")[0], gridOptions);
            if (spec.instance_id) {
                // @ts-ignore
                window[`ag_grid_${spec.instance_id}`] = gridOptions;
            }
        });

        return elem;
    }
};