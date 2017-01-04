
for file in $1/*
do
    tail -n+3 $file > temp1
    head -n-2 temp1 > temp2
    cut -d " " -f 2- temp2 > $file
done
rm temp*
