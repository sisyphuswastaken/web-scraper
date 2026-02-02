import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import '../styles/GraphVisualization.css';

const GraphVisualization = ({ graphData, loading, error }) => {
  const cyRef = useRef(null);
  const containerRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [layout, setLayout] = useState('cose');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (!graphData || !containerRef.current) return;

    const nodes = graphData.entities?.map(entity => ({
      data: {
        id: entity.id,
        label: entity.name,
        type: entity.type,
        properties: entity.properties || {},
        mentions: entity.mentions || 1
      }
    })) || [];

    const edges = graphData.relationships?.map((rel, idx) => ({
      data: {
        id: `edge-${idx}`,
        source: rel.source,
        target: rel.target,
        label: rel.type,
        type: rel.type
      }
    })) || [];

    const cy = cytoscape({
      container: containerRef.current,
      elements: [...nodes, ...edges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': (ele) => getNodeColor(ele.data('type')),
            'label': 'data(label)',
            'width': (ele) => Math.min(20 + (ele.data('mentions') || 1) * 5, 60),
            'height': (ele) => Math.min(20 + (ele.data('mentions') || 1) * 5, 60),
            'font-size': '12px',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#333',
            'text-outline-color': '#fff',
            'text-outline-width': 2,
            'border-width': 2,
            'border-color': '#666'
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#4CAF50',
            'background-color': '#81C784'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#999',
            'target-arrow-color': '#999',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'text-rotation': 'autorotate',
            'text-margin-y': -10,
            'color': '#666',
            'text-outline-color': '#fff',
            'text-outline-width': 1
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#4CAF50',
            'target-arrow-color': '#4CAF50',
            'width': 3
          }
        }
      ],
      layout: {
        name: layout,
        animate: true,
        animationDuration: 500
      }
    });

    cy.on('tap', 'node', (evt) => {
      const node = evt.target;
      setSelectedNode({
        id: node.data('id'),
        label: node.data('label'),
        type: node.data('type'),
        properties: node.data('properties'),
        mentions: node.data('mentions')
      });
    });

    cy.on('tap', (evt) => {
      if (evt.target === cy) {
        setSelectedNode(null);
      }
    });

    cy.on('zoom', () => {
      setZoomLevel(cy.zoom());
    });

    cyRef.current = cy;

    setStats({
      nodes: nodes.length,
      edges: edges.length,
      entityTypes: getEntityTypeCounts(graphData.entities || []),
      relationshipTypes: getRelationshipTypeCounts(graphData.relationships || [])
    });

    return () => {
      if (cyRef.current) {
        cyRef.current.destroy();
      }
    };
  }, [graphData, layout]);

  const getNodeColor = (type) => {
    const colors = {
      'PERSON': '#FF6B6B',
      'ORGANIZATION': '#4ECDC4',
      'LOCATION': '#45B7D1',
      'CONCEPT': '#FFA07A',
      'EVENT': '#98D8C8',
      'DATE': '#F7DC6F',
      'TECHNOLOGY': '#BB8FCE',
      'default': '#95A5A6'
    };
    return colors[type] || colors.default;
  };

  const getEntityTypeCounts = (entities) => {
    return entities.reduce((acc, entity) => {
      acc[entity.type] = (acc[entity.type] || 0) + 1;
      return acc;
    }, {});
  };

  const getRelationshipTypeCounts = (relationships) => {
    return relationships.reduce((acc, rel) => {
      acc[rel.type] = (acc[rel.type] || 0) + 1;
      return acc;
    }, {});
  };

  const handleZoom = (delta) => {
    if (cyRef.current) {
      const currentZoom = cyRef.current.zoom();
      cyRef.current.zoom({
        level: currentZoom + delta,
        renderedPosition: { x: containerRef.current.offsetWidth / 2, y: containerRef.current.offsetHeight / 2 }
      });
    }
  };

  const changeLayout = (layoutName) => {
    setLayout(layoutName);
    if (cyRef.current) {
      cyRef.current.layout({
        name: layoutName,
        animate: true,
        animationDuration: 500
      }).run();
    }
  };

  const fitGraph = () => {
    if (cyRef.current) {
      cyRef.current.fit(50);
    }
  };

  const exportGraph = (format) => {
    if (!cyRef.current) return;

    if (format === 'png') {
      const png = cyRef.current.png({ scale: 2 });
      const link = document.createElement('a');
      link.download = 'knowledge-graph.png';
      link.href = png;
      link.click();
    } else if (format === 'json') {
      const data = JSON.stringify(graphData, null, 2);
      const blob = new Blob([data], { type: 'application/json' });
      const link = document.createElement('a');
      link.download = 'knowledge-graph.json';
      link.href = URL.createObjectURL(blob);
      link.click();
    }
  };

  if (loading) return null;
  if (error) return null;

  return (
    <div className="graph-visualization-container">
      <div className="graph-controls">
        <div className="control-group">
          <h3>Layout</h3>
          <div className="button-group">
            <button 
              className={`control-btn ${layout === 'cose' ? 'active' : ''}`}
              onClick={() => changeLayout('cose')}
              title="Force-directed layout"
            >
              🌐 Force
            </button>
            <button 
              className={`control-btn ${layout === 'circle' ? 'active' : ''}`}
              onClick={() => changeLayout('circle')}
              title="Circular layout"
            >
              ⭕ Circle
            </button>
            <button 
              className={`control-btn ${layout === 'grid' ? 'active' : ''}`}
              onClick={() => changeLayout('grid')}
              title="Grid layout"
            >
              ▦ Grid
            </button>
            <button 
              className={`control-btn ${layout === 'breadthfirst' ? 'active' : ''}`}
              onClick={() => changeLayout('breadthfirst')}
              title="Hierarchical layout"
            >
              🌳 Tree
            </button>
          </div>
        </div>

        <div className="control-group">
          <h3>Zoom</h3>
          <div className="button-group">
            <button className="control-btn" onClick={() => handleZoom(0.2)}>➕</button>
            <span className="zoom-level">{(zoomLevel * 100).toFixed(0)}%</span>
            <button className="control-btn" onClick={() => handleZoom(-0.2)}>➖</button>
            <button className="control-btn" onClick={fitGraph}>⊡ Fit</button>
          </div>
        </div>

        <div className="control-group">
          <h3>Export</h3>
          <div className="button-group">
            <button className="control-btn" onClick={() => exportGraph('png')}>
              🖼️ PNG
            </button>
            <button className="control-btn" onClick={() => exportGraph('json')}>
              📄 JSON
            </button>
          </div>
        </div>
      </div>

      <div className="graph-content">
        <div ref={containerRef} className="graph-canvas"></div>

        {selectedNode && (
          <div className="node-details-panel">
            <div className="panel-header">
              <h3>Node Details</h3>
              <button 
                className="close-btn" 
                onClick={() => setSelectedNode(null)}
              >
                ✕
              </button>
            </div>
            <div className="panel-content">
              <div className="detail-row">
                <span className="detail-label">Name:</span>
                <span className="detail-value">{selectedNode.label}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Type:</span>
                <span className="detail-badge" style={{ backgroundColor: getNodeColor(selectedNode.type) }}>
                  {selectedNode.type}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Mentions:</span>
                <span className="detail-value">{selectedNode.mentions}</span>
              </div>
              {selectedNode.properties && Object.keys(selectedNode.properties).length > 0 && (
                <div className="detail-section">
                  <h4>Properties:</h4>
                  {Object.entries(selectedNode.properties).map(([key, value]) => (
                    <div key={key} className="property-row">
                      <span className="property-key">{key}:</span>
                      <span className="property-value">{String(value)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {stats && (
          <div className="legend-panel">
            <h3>Legend</h3>
            <div className="legend-section">
              <h4>Entity Types ({stats.nodes})</h4>
              {Object.entries(stats.entityTypes).map(([type, count]) => (
                <div key={type} className="legend-item">
                  <span 
                    className="legend-color" 
                    style={{ backgroundColor: getNodeColor(type) }}
                  ></span>
                  <span className="legend-label">{type}</span>
                  <span className="legend-count">{count}</span>
                </div>
              ))}
            </div>
            <div className="legend-section">
              <h4>Relationships ({stats.edges})</h4>
              {Object.entries(stats.relationshipTypes).map(([type, count]) => (
                <div key={type} className="legend-item">
                  <span className="legend-arrow">→</span>
                  <span className="legend-label">{type}</span>
                  <span className="legend-count">{count}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GraphVisualization;