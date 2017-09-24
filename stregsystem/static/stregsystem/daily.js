var chart = c3.generate({
	bindto: "#sales_chart",
    data: {
		x: "day",
        url: '../sales_api',
		mimeType: 'json',
		type: "area-spline",
		axes: {
			sales: "y",
			revenue: "y2",
		}
    },
	axis: {
		x: {
			type: 'timeseries',
			tick: {
				format: '%Y-%m-%d',
			},
		},
		y: {
			label: "Sales",
		},
		y2: {
			show: true,
			label: "Revenue",
		}
	}
});
