import { Card, Empty } from 'antd';
import ReactECharts from 'echarts-for-react';

export interface TestTrendData {
  date: string;
  passed: number;
  failed: number;
  total: number;
}

export interface TestTrendChartProps {
  data: TestTrendData[];
  title?: string;
  height?: number;
}

export function TestTrendChart({
  data,
  title = '测试趋势',
  height = 300,
}: TestTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card title={title}>
        <Empty description="暂无数据" />
      </Card>
    );
  }

  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    legend: {
      data: ['通过', '失败', '总计'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.date),
      axisLabel: {
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
    },
    series: [
      {
        name: '通过',
        type: 'line',
        smooth: true,
        data: data.map((d) => d.passed),
        itemStyle: {
          color: '#52c41a',
        },
        areaStyle: {
          color: 'rgba(82, 196, 26, 0.1)',
        },
      },
      {
        name: '失败',
        type: 'line',
        smooth: true,
        data: data.map((d) => d.failed),
        itemStyle: {
          color: '#ff4d4f',
        },
        areaStyle: {
          color: 'rgba(255, 77, 79, 0.1)',
        },
      },
      {
        name: '总计',
        type: 'bar',
        data: data.map((d) => d.total),
        itemStyle: {
          color: 'rgba(24, 144, 255, 0.5)',
        },
        barWidth: '30%',
      },
    ],
  };

  return (
    <Card bodyStyle={{ padding: 16 }}>
      <ReactECharts option={option} style={{ height }} />
    </Card>
  );
}

export interface PassRateChartProps {
  passed: number;
  failed: number;
  title?: string;
  height?: number;
}

export function PassRateChart({
  passed,
  failed,
  title = '通过率',
  height = 250,
}: PassRateChartProps) {
  const total = passed + failed;
  const rate = total > 0 ? ((passed / total) * 100).toFixed(1) : 0;

  const option = {
    title: {
      text: `通过率 ${rate}%`,
      subtext: `通过 ${passed} / 失败 ${failed}`,
      left: 'center',
      top: '35%',
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: '25%',
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
          },
        },
        data: [
          {
            value: passed,
            name: '通过',
            itemStyle: {
              color: '#52c41a',
            },
          },
          {
            value: failed,
            name: '失败',
            itemStyle: {
              color: '#ff4d4f',
            },
          },
        ],
      },
    ],
  };

  return (
    <Card bodyStyle={{ padding: 16 }}>
      <ReactECharts option={option} style={{ height }} />
    </Card>
  );
}

export interface TestTypeDistributionProps {
  data: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  title?: string;
  height?: number;
}

export function TestTypeDistribution({
  data,
  title = '测试类型分布',
  height = 250,
}: TestTypeDistributionProps) {
  if (!data || data.length === 0) {
    return (
      <Card title={title}>
        <Empty description="暂无数据" />
      </Card>
    );
  }

  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: '25%',
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: true,
          formatter: '{b}\n{c}',
        },
        data: data.map((d) => ({
          value: d.value,
          name: d.name,
          itemStyle: {
            color: d.color,
          },
        })),
      },
    ],
  };

  return (
    <Card bodyStyle={{ padding: 16 }}>
      <ReactECharts option={option} style={{ height }} />
    </Card>
  );
}

export interface ExecutionTimeChartProps {
  data: Array<{
    name: string;
    avgTime: number;
    minTime: number;
    maxTime: number;
  }>;
  title?: string;
  height?: number;
}

export function ExecutionTimeChart({
  data,
  title = '执行时间统计 (ms)',
  height = 300,
}: ExecutionTimeChartProps) {
  if (!data || data.length === 0) {
    return (
      <Card title={title}>
        <Empty description="暂无数据" />
      </Card>
    );
  }

  const option = {
    title: {
      text: title,
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    legend: {
      data: ['平均', '最小', '最大'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.name),
      axisLabel: {
        rotate: 45,
      },
    },
    yAxis: {
      type: 'value',
    },
    series: [
      {
        name: '平均',
        type: 'bar',
        data: data.map((d) => d.avgTime),
        itemStyle: { color: '#1890ff' },
        barWidth: '20%',
      },
      {
        name: '最小',
        type: 'bar',
        data: data.map((d) => d.minTime),
        itemStyle: { color: '#52c41a' },
        barWidth: '20%',
      },
      {
        name: '最大',
        type: 'bar',
        data: data.map((d) => d.maxTime),
        itemStyle: { color: '#ff4d4f' },
        barWidth: '20%',
      },
    ],
  };

  return (
    <Card bodyStyle={{ padding: 16 }}>
      <ReactECharts option={option} style={{ height }} />
    </Card>
  );
}

export default TestTrendChart;
