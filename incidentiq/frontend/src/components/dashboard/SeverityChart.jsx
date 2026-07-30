import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";

import Card from "../common/Card";
import EmptyState from "../common/EmptyState";
import { SEVERITY_COLORS, tooltipStyle } from "./chartTheme";

export default function SeverityChart({ data = [] }) {
  const total = data.reduce((sum, entry) => sum + entry.count, 0);

  return (
    <Card title="Incidents by severity" actions={<span className="is-muted">{total} total</span>}>
      {data.length === 0 ? (
        <EmptyState title="No severity data" />
      ) : (
        <ResponsiveContainer width="100%" height={270}>
          <PieChart>
            <Pie
              data={data}
              dataKey="count"
              nameKey="severity"
              innerRadius={62}
              outerRadius={96}
              paddingAngle={2}
              stroke="none"
            >
              {data.map((entry) => (
                <Cell key={entry.severity} fill={SEVERITY_COLORS[entry.severity] ?? "#8b98a5"} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle.contentStyle} itemStyle={tooltipStyle.itemStyle} />
            <Legend iconType="circle" />
          </PieChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
