document.addEventListener('DOMContentLoaded', function () {
    const COLORS = ['#9ACD32', '#A52A2A', '#5B9AA0', '#FFA500', '#622569',
            '#BC8F8F', '#808080', '#006400', '#191970', '#8B4513'],
          btn_query_plan = document.createElement("button"),
          yasqe = new Yasqe(document.getElementById('yasqe'), {
              persistenceId: null,
              tabSize: 2,
              indentUnit: 2,
              extraKeys: {
                  Tab: function(cm) {
                      cm.replaceSelection(new Array(cm.getOption('indentUnit') + 1).join(' '));
                  }
              },
              pluginButtons: function() { return btn_query_plan }
          }),
          errorEl = document.getElementById('plan-error'),
          endpoint = document.getElementById('yasqe').dataset.endpoint,
          nativeBtn = document.querySelector('.yasqe_queryButton:not(#btn_query_plan)');

    btn_query_plan.innerHTML = nativeBtn.innerHTML;
    nativeBtn.remove();

    function renderError(message) {
        errorEl.innerHTML = '';
        const alertEl = document.createElement('div');
        alertEl.className = 'alert alert-danger';
        alertEl.textContent = message;
        errorEl.appendChild(alertEl);
    }

    function clearError() {
        errorEl.innerHTML = '';
    }

    btn_query_plan.id = "btn_query_plan";
    btn_query_plan.title = "Create Plan";
    btn_query_plan.classList.add("yasqe_queryButton");
        btn_query_plan.onclick = function() {
        const query = yasqe.getValue(),
              canvas = document.getElementById('canvas'),
              queryPlanDetails = document.getElementById('details');

        canvas.innerHTML = '';
        queryPlanDetails.innerHTML = '';
        clearError();
        btn_query_plan.classList.add('busy');
        btn_query_plan.disabled = true;

        const body = new URLSearchParams({ query: query });

        fetch(endpoint, {
            method: 'POST',
            headers: { 'Accept': 'application/json' },
            body: body
        })
        .then(function(response) {
            if (!response.ok) {
                return response.text().then(function(text) {
                    throw { status: response.status, message: text };
                });
            }
            return response.json();
        })
        .then(function(data) {
            queryPlanDetails.innerHTML = '<h3>Sub-query Details:</h3><ul id="#subqueries"></ul>';
            create_tree(data['tree'], data['details']);
        })
        .catch(function(err) {
            renderError('The server returned with status code ' + err.status + '. Message: ' + err.message);
            console.log(err.status + ': ' + err.message);
        })
        .finally(function() {
            btn_query_plan.classList.remove('busy');
            btn_query_plan.disabled = false;
        });
    };

    function create_tree(treeData, details) {
        const ssq_list = document.getElementById("#subqueries"),
              endpoints = new Set();

        for (const ssq in details) {
            const child = document.createElement("li");
            child.innerHTML = "<b>" + ssq + "</b><br>Endpoint: " + details[ssq]["endpoint"] + "<br>Triples:<br>&nbsp;&nbsp;&nbsp;&nbsp;" + details[ssq]["triples"].replace(/\n/g, "<br>&nbsp;&nbsp;&nbsp;&nbsp;");
            ssq_list.appendChild(child);
            endpoints.add(details[ssq]["endpoint"]);
        }

        const endpoints_list = Array.from(endpoints);
        endpoints_list.sort();

        // set the dimensions and margins of the diagram
        const margin = {top: 20, right: 90, bottom: 30, left: 90},
              width  = 800 - margin.left - margin.right,
              height = 600 - margin.top - margin.bottom,
              node_size = 10;

        // declares a tree layout and assigns the size
        const treemap = d3.tree().size([width, height]);

        //  assigns the data to a hierarchy using parent-child relationships
        let nodes = d3.hierarchy(treeData, d => d.children);

        // maps the node data to the tree layout
        nodes = treemap(nodes);

        // append the svg object to the body of the page
        // appends a 'group' element to 'svg'
        // moves the 'group' element to the top left margin
        const svg = d3.select("#canvas").append("svg")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom),
            g = svg.append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        // adds the links between the nodes
        g.selectAll(".link")
            .data(nodes.descendants().slice(1))
            .enter().append("path")
            .attr("class", "link")
            .attr("d", d => {
                return "M" + d.x + "," + d.y
                    + "C" + (d.x + d.parent.x) / 2 + "," + d.y
                    + " " + (d.x + d.parent.x) / 2 + "," + d.parent.y
                    + " " + d.parent.x + "," + d.parent.y;
            });

        // adds each node as a group
        const node = g.selectAll(".node")
            .data(nodes.descendants())
            .enter().append("g")
            .attr("class", d => "node" + (d.children ? " node--internal" : " node--leaf"))
            .attr("transform", d => "translate(" + d.x + "," + d.y + ")");

        // adds the circle to the node
        node.append("circle")
            .attr("r", node_size)
            .style("fill", d => d.data.endpoint ? COLORS[endpoints_list.indexOf(d.data.endpoint) % COLORS.length] : "#fff");

        // adds the text to the node
        node.append("text")
            .attr("dy", ".35em")
            .attr("x", d => d.children ? (node_size + 5) * -1 : node_size + 5)
            .attr("y", d => d.children && d.depth !== 0 ? -(node_size + 5) : 0)
            .style("text-anchor", d => d.children ? "end" : "start")
            .text(d => d.data.name);
    }
}); // end DOMContentLoaded