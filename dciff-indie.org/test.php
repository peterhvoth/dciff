<html>
<head>
	<title>DCIFF DB Test</title>
</head>
<body>
<h3>DB Results</h3>
<?php
if (preg_match('ip(?:-\d+){4}\.[\w-]+\.compute', gethostname())) {
    $conn = new mysqli("main.caqmcqa1ulqd.us-east-2.rds.amazonaws.com", "webuser", "", "wab");
} else {
    $conn = new mysqli("localhost", "webuser", "", "wab");
}

$stmt = $conn->prepare("SELECT * FROM film WHERE id=?");
$stmt->bind_param("i", $_GET['film_id']);
$stmt->execute();
$result = mysqli_fetch_assoc($stmt->get_result());

$title = $result['title_original']!='' & $result['title_original']!=$result['title_english'] ? $result['title_english'] . ' (' . $result['title_original'] . ')' : $result['title_english'];

if ($result['synopsis_250_word']!='') {
    $result['synopsis'] =  $result['synopsis_250_word'];
} elseif ($result['synopsis_125_word']!='') {
    $result['synopsis'] =  $result['synopsis_125_word'];
} elseif ($result['synopsis_3_line']!='') {
    $result['synopsis'] =  $result['synopsis_3_line'];
} else {
    $result['synopsis'] =  $result['logline'];
}
?>
<h1><?php echo $title; ?></h1>
<p><?php echo $result['synopsis']; ?></p>

<?php mysqli_close($conn); ?>
</body>
</html>
