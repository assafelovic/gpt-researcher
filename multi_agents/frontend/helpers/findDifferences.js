function findDifferences(obj1, obj2) {
    function isObject(obj) {
        return obj && typeof obj === 'object' && !Array.isArray(obj);
    }

    function compareObjects(o1, o2) {
        const changes = {};

        for (const key in o1) {
            if (isObject(o1[key]) && isObject(o2[key])) {
                const nestedChanges = compareObjects(o1[key], o2[key]);
                if (Object.keys(nestedChanges).length > 0) {
                    changes[key] = nestedChanges;
                }
            } else if (Array.isArray(o1[key]) && Array.isArray(o2[key])) {
                if (o1[key].length !== o2[key].length || o1[key].some((val, index) => val !== o2[key][index])) {
                    changes[key] = { before: o1[key], after: o2[key] };
                }
            } else {
                if (o1[key] !== o2[key]) {
                    changes[key] = { before: o1[key], after: o2[key] };
                }
            }
        }

        for (const key in o2) {
            if (!(key in o1)) {
                changes[key] = { before: undefined, after: o2[key] };
            }
        }

        return changes;
    }

    return compareObjects(obj1, obj2);
}

export default findDifferences;