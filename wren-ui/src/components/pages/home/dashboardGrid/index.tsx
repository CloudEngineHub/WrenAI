import { useMemo } from 'react';
import GridLayout from 'react-grid-layout';
import styled from 'styled-components';

import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';

const StyledDashboardGrid = styled.div`
  width: 768px;
  margin-right: auto;
  margin-left: auto;
  background-color: var(--gray-3);
  border: 1px solid var(--gray-4);
  border-radius: 4px;

  .adm-pin-item {
    background-color: white;
    height: 100%;
    border-radius: 8px;
    border: 1px solid var(--gray-4);
    padding: 16px;
    box-shadow:
      rgba(0, 0, 0, 0.1) 0px 10px 15px -3px,
      rgba(0, 0, 0, 0.05) 0px 4px 6px -2px;
  }
`;

export default function DashboardGrid() {
  const gridLayouts = useMemo(() => {
    return [
      {
        id: 'a',
        layout: { x: 0, y: 0, w: 6, h: 6 },
        render: <div className="adm-pin-item">a</div>,
      },
      {
        id: 'b',
        layout: { x: 6, y: 0, w: 6, h: 6 },
        render: <div className="adm-pin-item">b</div>,
      },
    ];
  }, []);

  console.log(gridLayouts);

  const grids = gridLayouts.map((item) => {
    return (
      <div key={item.id} data-grid={item.layout}>
        {item.render}
      </div>
    );
  });

  console.log(grids);

  return (
    <StyledDashboardGrid className="mt-12">
      <GridLayout
        className="layout"
        cols={12}
        margin={[16, 16]}
        rowHeight={30}
        width={768}
      >
        {grids}
      </GridLayout>
    </StyledDashboardGrid>
  );
}
