<html>
<head>
	<title>DCIFF DB Test</title>
</head>
<body>
<h3>DB Results</h3>
<?php
echo gethostname();
foreach($_GET as $key => $val) {
	echo $key . " - " . $val . "<br>";
}
$conn = mysqli_connect("main.caqmcqa1ulqd.us-east-2.rds.amazonaws.com", "webuser", "", "wab");
$result = mysqli_query($conn,"SELECT * FROM film ORDER BY rand() LIMIT 3");
echo '<pre>';
while($row=mysqli_fetch_assoc($result)) {
	$tblEntries[] = $row;
	print_r($row);
}
echo '</pre>';
mysqli_close($conn);
?>
</body>
</html>
